#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

         🄯 {datetime.now().year} 
    '''

    name = 'snowflake'

    def __init__ (self):

        # show banner
        self.log(self.banner, 'blue')

        # process data
        self.jobs = {}
    
    def info_to_console (self):

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

    def new_job (self, func, args=(), name=None, operating_week_days='all', repeat=False, repeat_sleep=1):

        '''
        Adds a new job by provided variables.

        FORMAT
        operating_week_days: ['mon', 'tue', 'wed', 'thu', 'sat', 'sun']
        '''

        # id and name
        if not name: name = func.__name__
        job_id = binascii.b2a_hex(uniform(size=16))                 # create a random 16 char hex string
        #job_id = max(list(self.jobs.values()))+1

        # denote creation time
        created = datetime.utcnow()

        # create a process object
        wrap = lambda : self.wrapper(func, args=args, repeat=repeat, wait=repeat_sleep)
        process = Process(target=wrap)

        if operating_week_days != 'all':
            operating_week_days = [d.lower()[:3] for d in operating_week_days]

        # package
        self.jobs[job_id] = {
            "active": False,
            "disable": False,
            "id": job_id,
            "name": name,
            "operating_time_window": None,                          # e.g. ['12:30', '14:30']
            "operating_week_days": operating_week_days,
            "process": process,
            "repeat": True,
            "repeat_sleep": 0,
            "time_created": created,
            "time_started": None,
            "time_stopped": None
        }
    
    def manage (self):
        
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
            
        sleep(.1)
    
    def wrapper (self, func, args=(), repeat=False, wait=1):

        while True:

            func(*args)
            if not repeat:
                break
            else:
                sleep(wait)

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

    def _newJobRequest (self, requestObject):

        '''
        Creates a new entry in jobs object.
        '''

        '''
        Adds a new job by provided variables.

        FORMAT
        operating_week_days: ['mon', 'tue', 'wed', 'thu', 'sat', 'sun']
        '''

        # id and name
        if not name: name = func.__name__
        job_id = binascii.b2a_hex(uniform(size=16))                 # create a random 16 char hex string
        #job_id = max(list(self.jobs.values()))+1

        # denote creation time
        created = datetime.utcnow()

        # create a process object
        wrap = lambda : self.wrapper(func, args=args, repeat=repeat, wait=repeat_sleep)
        process = Process(target=wrap)

        if operating_week_days != 'all':
            operating_week_days = [d.lower()[:3] for d in operating_week_days]

        # package
        self.jobs[job_id] = {
            "active": False,
            "disable": False,
            "id": job_id,
            "name": name,
            "operating_time_window": None,                          # e.g. ['12:30', '14:30']
            "operating_week_days": operating_week_days,
            "process": process,
            "repeat": True,
            "repeat_sleep": 0,
            "time_created": created,
            "time_started": None,
            "time_stopped": None
        }


class APIHandler(http.server.BaseHTTPRequestHandler):

    
    '''
    The API handler is an http.server.BaseHTTPRequestHandler wrapper object
    and parent of the core. Interactions received from a request can reference
    the server core.

    ╔═════════════╗
    ║ http.server ║ Built-In
    ╚═════════════╝
            ║ 
        ╔══════════════╗
        ║ └ APIHandler ║ Extension (Snowflake)
        ║    └ Core    ║
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
        jsonPkg = json.loads(self.rfile.read(int(self.headers['Content-Length'])).decode('utf-8'))
        dic = json.loads(jsonPkg) # double loads turns to dict

        print('json package', dic)

    
    
    
class handler(http.server.SimpleHTTPRequestHandler):

    '''
    Main for handling json packages
    '''

    def do_POST(self):

        # send an ok first
        self.send_response(200)

        # send header
        self.send_header('Content-type', 'application/json')
        
        ctype, pdict = cgi.parse_header(self.headers['Content-Type'])
        
        # refuse to receive non-json content
        if ctype != 'application/json':
            self.send_response(400)
            self.end_headers()
            return
            
        # read the request message and convert it to json
        jsonPkg = json.loads(self.rfile.read(int(self.headers['Content-Length'])).decode('utf-8'))
        dic = json.loads(jsonPkg) # double loads turns to dict
        print('dic', dic)




PORT = 3000
with http.server.HTTPServer(('localhost', PORT), APIHandler) as srv:
    srv.serve_forever()