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

#  Please see also https://github.com/sidhantpanda/xkcd-api/blob/master/xkcd-api.js
# for help on referencing a particular comic

""" Thoughts on how this bot should work:
it should automatically post the most recent comic to the workspace,
any time a new comic comes out.  this would be defined as any new
comic that has not yet been posted or referred to in the log.

the user @mentions the bot,and a modal pops up
the modal shows the current xkcd comic, and
buttons like the xkcd website itself - forward, back, random, etc
there are also buttons to share to group and to share to an individual.
the bot will need to "sign" this comic with the user's name, so some OAuth
is needed i think... will have to look into this.

there should be a help section explaining how to use the bot -
accessible from commands and from a button on the modal.

the user should also be able to post with slash commands.

NICE TO HAVE:
scan the messages in the workspace for the mention of xkcd and pop up a
query to the poster ("would you like to post a comic?")

Thoughts on how to work this:
I'll need to keep track of what the most recent comic was.  I think we
could use logging with a message like "posted most recent comic # 1234."
in this situation, and have the bot read the log file on loading,
parse it for #1234, ping the xkcd, and print any comics that have a higher
number.

"""

"""A standalone Slack client implementation
see https: // slack.dev/python-slackclient/
"""


if sys.version_info[0] < 3:
    raise RuntimeError("This program requires Python 3")

load_dotenv()

# globals
goodbye_posted_flag = False
BOT_NAME = "while_xkcd"
BOT_CHAN = "#janell-bot-test"
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
    'show': ("Shows the comic indexed by the number"
             "immediately following 'show'."),
    'history': ("Prints the index number of"
                "the last X comics shown, where X is typed"
                "immediately after 'history'."),
    'api': 'Helpfully shows xkcd\'s api helpful documentation. Sort of.',
    'which': 'Which what?'
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


#  Uncomment below code to test that the app can post anything at all.
# slack_token = os.environ["BOT_USER_TOKEN"]
# client = WebClient(token=slack_token)

# client.chat_postMessage(
#     channel="#janell-bot-test",
#     text="Hello from your app! :tada:",
# )

# Create module logger from config file


def config_logger():
    """ Setup logging configuration """
    with open('logging.yaml') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    return logging.getLogger(__name__)


logger = config_logger()


class SlackClient:
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
        logger.info("Created new SlackClient Instance")

    def __repr__(self):
        return self.at_bot

    def __str__(self):
        return self.__repr__()

    def on_hello(self, **payload):
        """ When Slack has confirmed our connection request"""
        logger.info(f'{self} has connected to the Slack RTM server.')
        self.post_message(f'{self.name} is now online.')

    def on_message(self, **payload):
        """ Slack has sent a message to me"""
        data = payload['data']
        self.check_goodbye(data)
        if 'text' in data and self.at_bot in data['text']:
            # parse everything after the at_bot mention
            chan = data['channel']
            raw_command = data['text'].split(self.at_bot)[1].strip().lower()
            # handle the command
            response = self.handle_command(raw_command, chan)
            self.post_message(response, chan)

        logger.debug(data['text'])

    def handle_command(self, raw_command, chan):
        """Parses a raw command string directed at the bot"""
        response = None
        args = raw_command.split(" ")
        cmd = args[0]
        logger.info(f'{self} Received command "{raw_command}"')

        if cmd == 'raise':
            response = "Manual exception handler test"
            raise Exception("Manual exception handler test.")
        elif cmd not in bot_commands:
            response = (f"'{cmd}' doesn\'t mean anything to me."
                        "  Try 'help' for a list of commands.")
            logger.error(f'{self} Unknown command: {cmd}')

        elif cmd == 'help':
            response = "Available commands: \n" + formatted_dict(bot_commands)
        elif cmd == 'ping':
            response = f'{self.name} has been running for {self.get_uptime()}.'
        elif cmd == 'exit' or cmd == 'quit':
            logger.warning('Manual exit requested.')
            response = f'See you next time!'

        elif cmd == 'first':
            # FIXME

            pass
        elif cmd == 'last':
            # TODO
            pass
        elif cmd == 'previous':
            # TODO
            pass
        elif cmd == 'next':
            # TODO
            pass
        elif cmd == 'random':
            # TODO
            pass
        elif cmd == 'show':
            # TODO
            pass
        elif cmd == 'history':
            # TODO
            pass
        elif cmd == 'api':
            # TODO
            pass
        elif cmd == 'which':
            response = f'I have no idea, sorry.  Which what?'

        return response

    def on_goodbye(self, **payload):
        self.post_message('Goodbye, cruel world...')
        logger.warning('f{self} is disconnecting.')

    def post_message(self, message, chan=BOT_CHAN):
        """Sends a message to a Slack channel"""
        # make sure that we have an actual WebClient instance
        print('entry to post_message:', message)

        assert self.sc._web_client is not None
        with self.msg_lock:
            print('inside msg lock, message :', message)
            if message:
                self.sc._web_client.chat_postMessage(
                    channel=chan,
                    text=message
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
    slackclient = SlackClient(
        os.environ['BOT_USER_TOKEN'],
        os.environ['BOT_USER_ID']).run()


if __name__ == '__main__':
    main(sys.argv[1:])
    print("completed - done with everything")
