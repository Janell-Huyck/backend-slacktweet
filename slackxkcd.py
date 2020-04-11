#!/usr/bin/env python3
"""A Slackbot implementation that integrates Slack and Twitter clients together"""


from slack_client import SlackClient
from twitter_client import TwitterClient


def config_logger():
    """ Setup logging configuration """
    with open('logging.yaml') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    return logging.getLogger(__name__)


logger = config_logger()


def main():
    pass


if __name__ == '__main__':
    main()
