#!/usr/bin/env python3

import sys
import logging
import logging.config
import yaml
from dotenv import load_dotenv
import requests
from random import randint

# Guard against python2
if sys.version_info[0] < 3:
    raise RuntimeError("Python 3 is required")

load_dotenv()

# Create module logger from config file


def config_logger():
    """ Setup logging configuration """
    with open('logging.yaml') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    return logging.getLogger(__name__)


logger = config_logger()


class XkcdApi:

    def __init__(self):
        self.base_url = 'https://www.xkcd.com/'
        self.json_ending = '/info.0.json'
        self.comic_api_help = '1481'
        self.get_random_api = 'random'
        self.first = '1'
        self.last = str(requests.get(
            self.base_url + self.json_ending).json()["num"])

    def construct_url(self, request):
        """ Changes a descriptive request into a gettable url"""

        if (isinstance(request, int) and
                request > 0 and request < int(self.last)):
            url = self.base_url + str(request) + self.json_ending
        elif request == 'random':
            url = self.base_url + \
                str(randint(1, int(self.last))) + self.json_ending
        elif request == 'first':
            url = self.base_url + self.first + self.json_ending
        elif request == 'last':
            url = self.base_url + self.last + self.json_ending
        else:
            return "invalid"
        return url

    def handle_comic_request(self, request):
        """ Returns a comic json object, given a descriptive request"""
        nonworking_links = [404, 1663]
        comic_not_found = 1969  # returns a comic about a 404 error

        if request in nonworking_links:
            request = comic_not_found

        if isinstance(request, int) or request in ['first', 'last', 'random']:
            comic_json_url = self.construct_url(request)
            if comic_json_url == "invalid":
                comic_json_url = self.construct_url(comic_not_found)
            comic_object = requests.get(
                comic_json_url).json()
        else:
            return self.handle_comic_request(comic_not_found)
        blocks = self.construct_blocks(comic_object)
        comic_number = comic_object['num']
        return comic_number, blocks

    def construct_blocks(self, comic_object):
        """ Returns the JSON format block object used for printing in Slack"""

        blocks = [{
            "type": "image",
            "title": {
                "type": "plain_text",
                "text": comic_object['title']
            },
            "image_url": comic_object['img'],
            "alt_text": comic_object['alt']
        }
        ]
        return blocks
