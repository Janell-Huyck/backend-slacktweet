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
        # Comic '404' can't be found - it's a joke.
        if request == 404:
            request = 1969
        if isinstance(request, int) or request in ['first', 'last', 'random']:
            comic_json_url = self.construct_url(request)
            if comic_json_url == "invalid":
                comic_json_url = self.construct_url(1969)
            comic_object = requests.get(
                comic_json_url).json()
        # Called when for some reason xkcd can't return the json request.
        # Seems to happen a lot for the most recent comics.
        else:
            return self.handle_comic_request(1969)

        return comic_object

    def get_comic(self, url):
        """ Returns a comic object, given the url """
        return requests.get(url).json()


def main(*args):

    xkcd = XkcdApi()


if __name__ == '__main__':
    main(sys.argv[1:])
