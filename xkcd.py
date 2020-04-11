#!/usr/bin/env python3

import os
import sys
import datetime as dt
import time
import logging
import logging.config
import yaml
from dotenv import load_dotenv
import requests

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
        self.json_ending = 'info.0.json'
        self.comic_api_help = '1481/'
        self.get_random_api = 'random/'
        self.first = '1/'
        self.last = requests.get(
            self.base_url + self.json_ending).json()["num"]

    def construct_url(self, request):
        """ Changes a descriptive request into a gettable url"""
        if isinstance(request, int) and request > 0 and request < self.last:
            url = self.base_url + str(request) + self.json_ending
        elif request == 'random':
            url = self.base_url + self.get_random_api + self.json_ending
        elif request == 'first':
            url = self.base_url + self.first + self.json_ending
        elif request == 'last':
            url = self.base_url + self.last + self.json_ending
        else:
            return "invalid"
        return url

    def handle_comic_request(self, request):
        """ Returns a comic number and image, given a descriptive request"""
        if request == 404:
            request = 1969
        url = self.construct_url(request)
        if url == "invalid":
            return self.handle_comic_request(1969)
        comic = self.get_comic(url)
        return (comic['num'], comic['img'])

    def get_comic(self, url):
        """ Returns a comic object, given the url """
        return requests.get(url).json()


def main(*args):

    xkcd = XkcdApi()
    print(xkcd.last)


if __name__ == '__main__':
    main(sys.argv[1:])
    print("completed - done with xkcd")
