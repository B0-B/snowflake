#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from backend.core import Core
from numpy.random import randint
from traceback import format_exc
from pathlib import Path
import http.server, cgi
import json

__root__ = str(Path(__file__).parent.parent.resolve()) 

# instantiate the core to fix the pointers
__core__ = Core()


class APIHandler(http.server.BaseHTTPRequestHandler):

    '''
    The API handler is an http.server.BaseHTTPRequestHandler wrapper object
    and parent of the core. Interactions received from a request can reference
    the server core.

    ╔═════════════╗
    ║ http.server ║ Built-In
    ╚═════════════╝
            ║ 
        ╔══════════════╗ Snowflake
        ║ └ APIHandler ║ [BaseHTTRequestHandler]                            
        ║    ├ Core    ║ 
        ║    |   ║     ║                  ╔════════╗
        ║    |   ║     ║ <--------------> ║ Client ║
        ║    |   ║     ║                  ╚════════╝
        ║    └ do_POST ║ 
        ╚══════════════╝ 
    '''

    Core = __core__
    def do_POST (self):

        self.Core.log(f"New request by {self.client_address[0]} ...")

        # initialize the response object first.
        # this object will be filled throughout the protocol
        # and then send back to client.
        responseObject = {'response': '', 'errors': []}

        # communicate header
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        ctype, _ = cgi.parse_header(self.headers['Content-Type'])
        
        # reject non-json content
        if ctype != 'application/json':
            self.send_response(400)
            self.end_headers()
            return

        # extract json package
        # double json.loads() turns to dict type, 
        # this dictionary will be the extracted request object
        #print('headers', self.headers) # for testing
        jsonPkg = json.loads(self.rfile.read(int(self.headers['Content-Length'])).decode('utf-8'))
        requestObject = json.loads(jsonPkg) 

        try:

            '''
            determine request type
                - request: will add a request object
                - ls: list all jobs with info
                - set: set a specific argument
            '''
            if requestObject['request'].lower() == 'ls':
                responseObject['response'] = self.Core._list()
            elif requestObject['request'].lower() == 'deploy':
                self.Core.log(f"Deploying new job ...", 'y')
                success, info = self.Core.deploy(requestObject)
                if success:
                    msg = f"Successfully deployed new cron job process '{requestObject['name']}'"
                    responseObject['response'] = msg
                else:
                    self.Core.log(info, 'red')  
                    responseObject['errors'].append(info)      
            elif requestObject['request'].lower() == 'disable':
                if 'name' in requestObject:
                    identifier = requestObject['name']
                    if not self.Core._findIdByName(identifier):
                        responseObject['errors'].append(f"Identifier '{identifier}' not found.")
                elif 'id' in requestObject:
                    identifier = requestObject['id']
                    if identifier not in self.jobs:
                        responseObject['errors'].append(f"Identifier '{identifier}' not found.")
                else:
                    err = f"No identifier (name, or id needed) provided."
                    responseObject['errors'].append(err)
                # disable the job if the identifier search yields no errors
                if len(responseObject['errors']) == 0:
                    self.Core.disable(identifier)
            elif requestObject['request'].lower() == 'ping':
                responseObject['response'] = self.Core.ping_response
            elif requestObject['request'].lower() == 'config':
                self.Core.log(f"{self.client_address[0]} requested an argument change in '{requestObject['name']}' job.", 'y')
                # get the correct id of the job depending on variables
                if 'name' in requestObject:
                        id = self.Core._findIdByName(requestObject['name'])
                elif 'id' in requestObject:
                        id = requestObject['id']
                else:
                        raise KeyError('No name nor id was provided!')    
                # unpack the argument and value
                arg, val = requestObject['argument']
                # apply
                self.Core.jobs[id][arg] = val       
            else:
                self.send_response(403)
            
        except:
            
            # inform the client that an exception occured, without details.
            err = f'An exception occured during the request.'
            requestObject['errors'].append(err)
            # log server-side console with details.
            self.Core.log(err + '\n' + format_exc(), 'red') 

        finally:

            # log output in server-side console
            if len(responseObject['response']) > 0:
                self.Core.log(responseObject['response'], 'y')
            if len(responseObject['errors']) > 0:
                self.Core.log(responseObject['errors'][0], 'red')

            # send the response object
            self.end_headers()
            self.wfile.write(json.dumps(responseObject).encode('utf-8'))

class WebHandler(http.server.BaseHTTPRequestHandler):

    '''
    Casts a web interface to communicate more easily with api.
    '''

    Core = __core__
    def do_POST (self):
        
        # communicate header
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=UTF-8')
        ctype, _ = cgi.parse_header(self.headers['Content-Type'])
        
        # reject non-json content
        if ctype != 'application/json':
            self.send_response(400)
            self.end_headers()
            return