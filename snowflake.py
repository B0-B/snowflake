#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from backend.handlers import APIHandler, WebHandler
from backend.pipe import pipe
import socketserver
import json

'''
Main orchestration of handlers for snowflake server.
'''

if __name__ == '__main__':

    with open('config.json') as f:

        # load config
        conf = json.load(f)

        # define endpoints
        __api__ = socketserver.TCPServer((conf["host"], conf["port_api"]), APIHandler)
        __web__ = socketserver.TCPServer((conf["host"], conf["port"]), WebHandler)

        thread_api = pipe(__api__.serve_forever, 0)
        thread_web = pipe(__web__.serve_forever, 0)

        # start the threads
        thread_api.start()
        print('started api endpoint on port:', conf["port_api"])
        thread_web.start()
        print('started web endpoint on port:', conf["port"], f'\nvisit https://{conf["host"]}:{conf["port"]}')