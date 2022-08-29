#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
from multiprocessing import Process
from datetime import datetime
from numpy.random import uniform, choice
import binascii
from time import sleep
import http.server, ssl, cgi
import json

class Core:

    '''
    A shell level interface to an http.server-compliant cron-job handler.
    Schedules, deploys and monitors jobs with quick access into the process. 
    '''


    banner=f'''
         ..    ..    
         '\    /'     
           \\\\//       
      _.__\\\\\///__._  
       '  ///\\\\\  '   
           //\\\\       
         ./    \.     
         ''    ''

    s n o w  f l a k e

         🄯 {min([2022, datetime.now().year])} 
    '''

    name = 'snowflake'

    def __init__ (self):

        # show banner
        self.log(self.banner, 'blue')

        # process data
        self.jobs = {}

        # API and request parameters
        self.mandatory_parameters = ['name', 'target_path', 'command']
    
    def list_to_console (self):

        '''
        A dashboard-like summary output of all deployed jobs.
        '''

        print('job name\tstatus\tcreated\tjob id')
        for id, job in self.jobs.items():
            a_col = '\033[92m'
            if not job["status"]: 
                a_col = '\033[91m'
            print(f'{job["name"]}\t{a_col}{job["status"]}\033[0m\t{job["time_created"]}\t{id}')

    def log (self, stdout, color='', indent=0, end='\n'):

        '''
        A simple logger method which allows to direct all outputs to console, file etc.
        '''

        color = color.lower()

        if indent > 0:
            head = ''
            indent = ''.join(['\t']*indent)
        else:
            head = f'\033[96m[ {self.name} | {datetime.today().strftime("%m-%d-%Y %H:%M:%S")} ]\033[0m\t'
            indent = ''
        if 'green' in color:
            color = '\033[92m'
        elif 'red' in color:
            color = '\033[91m'
        elif 'y' in color[:1]:
            color = '\033[93m'
        elif 'blue' in color:
            color = '\033[96m'
        else:
            color = '\033[0m'
        print(f'{head}{indent}{color}{stdout}\033[0m', end=end)
    
    
    def newJob (self, requestObject):

        '''
        Creates a new entry in jobs object.
        
        Adds a new job by provided variables.

        FORMAT
        operating_week_days: ['mon', 'tue', 'wed', 'thu', 'sat', 'sun']

        RETURN
        (bool, string)-tuple
        The bool value will be true if the request was accepted, otherwise False 
        and the string will serve as info message.
        '''

        stdout = ''


        ''' Request Policy Check '''
        # -- mandatory parameters --
        for p in self.mandatory_parameters:
            if p not in requestObject:
                stdout = f'Key "{p}" not specified, the mandatory request parameters are {self.mandatory_parameters}'
                return False, stdout

        # -- optional parameters --
        if "active" in requestObject:
            active = requestObject["active"]
            if type(active) is not bool:
                stdout = f"active must be boolean!"
        else:
            active = False
        if "disable" in requestObject:
            disable = requestObject["disable"]
            if type(disable) is not bool:
                stdout = f"disable must be boolean!"
        else:
            disable = False
        if "operating_time_window" in requestObject:
            operating_time_window = requestObject["operating_time_window"]
            if len(operating_time_window) != 2 or ':' not in operating_time_window[0] or ':' not in operating_time_window[1]:
                stdout = f"'operating_time_window' wrongly specified! Need a valid time window e.g. '[12:00, 14:30]'"
        else:
            operating_time_window = None
        if "operating_week_days" in requestObject:
            if type(operating_week_days) is not list:
                stdout = f"'operating_week_days' must be a list of strings ['mon', 'tue',..]!"
            operating_week_days = [d.lower()[:3] for d in requestObject["operating_week_days"]]
        else:
            operating_week_days = 'all'
        if "repeat" in requestObject:
            repeat = requestObject["repeat"]
            if type(repeat) is not bool:
                stdout = f"repeat must be boolean!"
        else:
            repeat = False
        if "repeat_sleep" in requestObject:
            repeat_sleep = requestObject["repeat"]
            if type(repeat) is not int or repeat < 0:
                stdout = f"repeat_sleep must be a positive integer!"
        else:
            repeat_sleep = 0
        if stdout != '':
            return False, stdout

        # -- certain parameters --
        # the job id is a randomly generated 16 char hex string
        job_id = binascii.b2a_hex(uniform(size=16))
        # denote creation time
        time_created = datetime.utcnow()

        # create a process object
        wrap = lambda : self.wrapper(func, args=args, repeat=repeat, wait=repeat_sleep)
        process = Process(target=wrap)

        if operating_week_days != 'all':
            operating_week_days = [d.lower()[:3] for d in operating_week_days]

        # package
        self.jobs[job_id] = {
            "active": active,
            "disable": disable,
            "id": job_id,
            "name": requestObject['name'],
            "operating_time_window": operating_time_window,                 
            "operating_week_days": operating_week_days,
            "process": process,
            "repeat": True,
            "repeat_sleep": 0,
            "target_path": requestObject['target_path'],
            "time_created": time_created,
            "time_started": None,
            "time_stopped": None
        }

    # - private methods
    def _activateIfDeactivated (self, id):

        job = self.jobs[id]

        if not job['active']:
            job['active'] = True
        if not job['process'].is_alive():
            job['process'].start()
    
    def _deactivateIfActive (self, id):

        job = self.jobs[id]

        if job['active']:
            job['active'] = False
        if job['process'].is_alive():
            job['process'].terminate()

    def _manage (self):
        
        '''
        An automatic steering algorithm.
        The pipe respects the active variable in the job object only if the job is not disabled
        and will flip it according to the time operating window.
        '''

        current_hour = datetime.now().hour
        current_minute = datetime.now().minute
        week_day = datetime.today().strftime('%A').lower()[:3]

        for id, job in self.jobs.items():

            # skip this job if it is disabled on purpose,
            # also make sure everything is deactivated.
            if job['disabled']:
                self._deactivateIfActive(id)
                pass

            # check for weekday
            if job["operating_week_days"] != 'all' and week_day not in job["operating_week_days"]:
                self._deactivateIfActive(id)
                pass

            # check for time
            if current_hour < int(job["operating_time_window"][0].split(':')[0]) or current_hour > int(job["operating_time_window"][1].split(':')[0]):
                self._deactivateIfActive(id)
                pass
            else:
                if current_minute < int(job["operating_time_window"][0].split(':')[1]) or current_minute > int(job["operating_time_window"][1].split(':')[1]):
                    self._deactivateIfActive(id)
                    pass
                else:
                    self._activateIfDeactivated(id)

            # update final activity
            if job['active'] and not job['process'].is_alive():
                # initialize the multiprocessing process
                job['process'].start()
            elif not job['active'] and job['process'].is_alive():
                # stop the multiprocessing process
                job['process'].terminate()
            
    

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
    Core = Core()

    def do_POST (self):

        # communicate header
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        ctype, pdict = cgi.parse_header(self.headers['Content-Type'])

        # refuse to receive non-json content
        if ctype != 'application/json':
            self.send_response(400)
            self.end_headers()
            return

        # exctract json package
        # double loads turns to dict type, this dictionary
        # will be the extracted request object
        jsonPkg = json.loads(self.rfile.read(int(self.headers['Content-Length'])).decode('utf-8'))
        requestObject = json.loads(jsonPkg) 

        # determine request type
        if requestObject['request'].lower() == 'job':
            self.Core.log(f"new job request submitted ...", 'y')
            self.Core.newJob(requestObject)


PORT = 3000
with http.server.HTTPServer(('localhost', PORT), APIHandler) as srv:
    srv.serve_forever()