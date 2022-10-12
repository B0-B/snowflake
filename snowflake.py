#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from backend.handlers import APIHandler, WebHandler
from backend.pipe import pipe
import http.server, cgi
import json

'''
Main orchestration of handlers for snowflake server.
'''

if __name__ == '__main__':

    with open('config.json') as f:

        conf = json.load(f)
        print("config", conf)

        # define endpoints
        __api__ = http.server.HTTPServer((conf["host"], conf["port_api"]), APIHandler)
        __web__ = http.server.HTTPServer((conf["host"], conf["port"]), WebHandler)

        thread_api = pipe(__api__.serve_forever, 0)
        thread_web = pipe(__web__.serve_forever, 0)

        thread_api.start()
        thread_web.start()