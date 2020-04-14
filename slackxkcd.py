#!/usr/bin/env python3
"""A Slackbot implementation that integrates Slack and Xkcd clients together"""

import os
import sys
import argparse
import logging
import logging.config
import yaml

from dotenv import load_dotenv
from datetime import datetime as dt

from slack_client import SlackClient

load_dotenv()

# guard against Python 2
if sys.version_info[0] < 3:
    raise RuntimeError('This program requires Python 3+ to work.')


def config_logger():
    """ Setup logging configuration """
    with open('logging.yaml') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    return logging.getLogger(__name__)


def create_parser(args):
    parser = argparse.ArgumentParser(description='Slack and xkcd Together')
    parser.add_argument('-l', '--loglevel',
                        default='INFO',
                        help=('Desired logging level'
                              '(DEBUG, INFO, WARNING, ERROR)'))
    ns = parser.parse_args(args)
    return ns


def main(args):
    ns = create_parser(args)
    logger = config_logger()
    logger.setLevel(ns.loglevel)
    loglevel = logging.getLevelName(logger.getEffectiveLevel())
    app_start_time = dt.now()
    logger.info(
        '\n------------------------------------------------\n'
        f'          Running {__file__}\n'
        f'          Started on {app_start_time.isoformat()}\n'
        f'          PID is {os.getpid()}\n'
        f'          loglevel is {loglevel}\n'
        '-------------------------------------------------')

    with SlackClient(
        bot_user_token=os.environ['BOT_USER_TOKEN'],
        bot_id=os.environ['BOT_USER_ID']
    ) as bot:
        bot.run()

    uptime = dt.now() - app_start_time
    logger.info(
        '\n--------------------------------------------\n'
        f'         Stopped {__file__}\n'
        f'         Uptime was {str(uptime)}\n'
        '---------------------------------------------\n'
    )


if __name__ == '__main__':
    main(sys.argv[1:])
