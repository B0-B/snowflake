#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from backend.handlers import APIHandler
import socketserver
import json

'''
Main orchestration of handlers for snowflake server.
'''

if __name__ == '__main__':

    with open('config.json') as f:

        # load config
        conf = json.load(f)

        # define endpoint
        with socketserver.TCPServer((conf["host"], conf["port"]), APIHandler) as __web_api__:

            try:
                __web_api__.serve_forever()
            except KeyboardInterrupt:
                print('\nquit.')
                exit()