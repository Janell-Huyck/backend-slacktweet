#!/usr/bin/env python3

import yaml
import sys
import os
from slack import RTMClient, WebClient
from dotenv import load_dotenv
import logging.config
import logging
from datetime import datetime as dt
import signal
from threading import Lock
from xkcd import XkcdApi
import json

# Guard against Python 2
if sys.version_info[0] < 3:
    raise RuntimeError("This program requires Python 3")

load_dotenv()

# globals
goodbye_posted_flag = False
BOT_NAME = "while_xkcd"
BOT_CHAN = "#janell-bot-test"
WEBHOOK_URL = os.environ['WEBHOOK_URL']
bot_commands = {
    'help': 'Shows this helpful command reference.',
    'ping': 'Shows the uptime of this bot.',
    'exit': 'Shut down the entire bot. (Requires app restart)',
    'quit': 'Same as \'exit\'.',
    'first': 'Shows the first xkcd comic.',
    'last': 'Shows the most recent xkcd comic.',
    'previous': 'Shows the comic published prior to the one last shown.',
    'next': 'Shows the next comic published after the one last shown.',
    'random': 'Shows a random comic.',
    '[int]': 'Shows the comic indexed by the integer.',
    'history': ('Prints an orderd list of all'
                'comics shown since app restart.'),
    'api': 'Helpfully shows xkcd\'s api helpful documentation. Sort of.'
}


def formatted_dict(d, with_header=False):
    """Renders the contents of a dictionary into a preformatted string"""
    if d:
        # find the longest key entry in d or the header string
        width = max(map(len, d))
        lines = []
        if with_header:
            header_key = 'Date'
            header_value = 'Comic(s)'
            width = max(width, len(header_key))
            lines.extend([f'{header_key:<{width}} : {header_value}'])
        lines.extend([f'{k:<{width}} : {v}' for k, v in d.items()])
        return "```\n" + '\n'.join(lines) + "\n```"
    return "```<empty>```"


def config_logger():
    """ Setup logging configuration """
    with open('logging.yaml') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    return logging.getLogger(__name__)


logger = config_logger()


class SlackClient:
    """ A stand-alone Slack client that can post xkcd images to Slack"""

    def __init__(self, bot_user_token, bot_id=None):
        self.name = BOT_NAME
        self.bot_id = bot_id
        if not self.bot_id:
            # Read the bot's id by calling auth.test
            response = WebClient(token=bot_user_token).api_call('auth.test')
            self.bot_id = response['user_id']
            logger.info(f'My bot_id is {self.bot_id}')

        # Create an instance of the RTM client
        self.sc = RTMClient(token=bot_user_token, run_async=True)

        # Connect our callback events to the RTM client
        RTMClient.run_on(event="hello")(self.on_hello)
        RTMClient.run_on(event="message")(self.on_message)
        RTMClient.run_on(event="goodbye")(self.on_goodbye)

        # startup our client event loop
        self.future = self.sc.start()
        self.bot_start = dt.now()
        self.msg_lock = Lock()
        self.at_bot = f'<@{self.bot_id}>'
        self.comic_history = []
        logger.info("Created new SlackClient Instance")
        self.xkcd = XkcdApi()

    def __enter__(self):
        """ Allows this class to be used as a context manager."""
        logger.info("New Slack Client initiated.")
        return self

    def __exit__(self, type, value, traceback):
        """Implements context manager"""
        logger.info("Exiting the Slack Client.")

    def __repr__(self):
        return self.at_bot

    def __str__(self):
        return self.__repr__()

    def on_hello(self, **payload):
        """ When Slack has confirmed our connection request"""
        logger.info(f'{self} has connected to the Slack RTM server.')
        self.post_message(self.text_to_blocks(f'{self.name} is now online.'))

    def on_message(self, **payload):
        """ Slack has sent a message to me"""
        data = payload['data']
        self.check_goodbye(data)
        if 'text' in data and self.at_bot in data['text']:
            chan = data['channel']
            raw_command = data['text'].split(self.at_bot)[1].strip().lower()
            response = self.handle_command(raw_command, chan)
            self.post_message(response, chan)

    def handle_command(self, raw_command, chan):
        """Parses a raw command string directed at the bot"""
        response = None
        args = raw_command.split(" ")
        cmd = args[0]
        cmd = self.try_to_change_cmd_to_int(cmd)
        logger.info(f'{self} Received command "{raw_command}"')

        if cmd == 'raise':
            response = self.handle_raise()
        elif cmd == 'help':
            response = self.handle_help()
        elif cmd == 'ping':
            response = self.handle_ping()
        elif cmd == 'exit' or cmd == 'quit':
            response = self.handle_quit()
        elif isinstance(cmd, int) or cmd in ['first', 'last', 'random']:
            response = self.handle_comic_request(cmd)
        elif cmd == 'next':
            response = self.handle_next()
        elif cmd == 'previous':
            response = self.handle_previous()
        elif cmd == 'api':
            response = self.handle_api()
        elif cmd == 'history':
            response = self.handle_history()
        else:
            response = self.handle_not_command(cmd)
        return response

    def try_to_change_cmd_to_int(self, cmd):
        try:
            cmd = int(cmd)
        except Exception:
            pass
        finally:
            return cmd

    def handle_raise(self):
        response = self.text_to_blocks("Manual exception handler test")
        raise Exception("Manual exception handler test.")
        return response

    def handle_help(self):
        response = self.text_to_blocks(
            "Available commands: \n" + formatted_dict(bot_commands))
        return response

    def handle_ping(self):
        response = self.text_to_blocks(
            f'{self.name} has been running for {self.get_uptime()}.')
        return response

    def handle_quit(self):
        logger.warning('Manual exit requested.')
        response = self.text_to_blocks(f'See you next time!')
        return response

    def handle_comic_request(self, request):
        comic_number, blocks = self.xkcd.handle_comic_request(request)
        self.comic_history.append(comic_number)
        response = blocks
        return response

    def handle_next(self):
        if self.comic_history:
            response = self.handle_comic_request(
                int(self.comic_history[-1]) + 1)
        else:
            response = self.text_to_blocks(
                'I\'m sorry.  There must be a first to be a next.\n'
                'Please try this after you have requested a comic.')
        return response

    def handle_previous(self):
        if self.comic_history:
            response = self.handle_comic_request(
                int(self.comic_history[-1]) - 1)
        else:
            response = self.text_to_blocks(
                'I\'m sorry.  There must be a first to be a previous.\n'
                'Please try this after you have requested a comic.')
        return response

    def handle_api(self):
        # 1481 is xkcd's comic about API's
        response = self.handle_comic_request(1481)
        return response

    def handle_history(self):
        response = self.text_to_blocks(f'These are the comics shown since app restart:\
            \n {self.comic_history}')
        return response

    def handle_not_command(self, cmd):
        response = self.text_to_blocks(
            f"'{cmd}' doesn\'t mean anything to me.\n"
            "  Try 'help' for a list of commands.")
        logger.error(f'{self} Unknown command: {cmd}')
        return response

    def on_goodbye(self, **payload):
        """Slack has decided to terminate our instance"""
        self.post_message(self.text_to_blocks('Goodbye, cruel world...'))
        logger.warning('f{self} is disconnecting.')

    def text_to_blocks(self, message):
        blocks = [{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": message
            }
        }]
        return blocks

    def post_message(self, blocks=None, chan=BOT_CHAN):
        """Sends a message to a Slack channel"""
        # make sure that we have an actual WebClient instance
        assert self.sc._web_client is not None
        if blocks:
            blocks = json.dumps(blocks)
        self.sc._web_client.chat_postMessage(
            channel=chan,
            # text=message,
            as_user=False,
            blocks=blocks
        )

    def get_uptime(self):
        """ Return how long the client has been connected """
        return dt.now() - self.bot_start

    def check_goodbye(self, data):
        """ Checks incoming messages for goodbye messages
        from the bot.  If found, kills the bot."""

        if data.get('subtype') and (
                data['subtype'] == 'bot_message') and (
                data['text'] == 'See you next time!'):
            os.kill(os.getpid(), signal.SIGTERM)

    def run(self):
        """ Starts up the thread that watches Slack for messages"""
        logger.info("waiting for things to happen")
        loop = self.future.get_loop()
        # wait until ctrl-C or SIGTERM / SIGINT
        loop.run_until_complete(self.future)
        logger.info("done waiting for things. (end of 'run' function)")


def main(args):
    SlackClient(
        os.environ['BOT_USER_TOKEN'],
        os.environ['BOT_USER_ID']).run()


if __name__ == '__main__':
    main(sys.argv[1:])
    logger.info("completed - done with everything")
