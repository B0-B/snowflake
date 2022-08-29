#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
from multiprocessing import Process
from subprocess import Popen, PIPE
from datetime import datetime
from numpy.random import uniform, choice, randint
from traceback import format_exc, print_exc
import binascii
from time import sleep
import http.server, ssl, cgi
import json

class Job:

    '''
    API to steer and trace the Job on kernel level.
    '''

    def __init__ (self, requestObject):

        # check and apply operating arguments
        self.id = self._checkArgAndAssign('id', str, '', requestObject, mandatory=True)
        self.target_path = self._checkArgAndAssign('target_path', str, '', requestObject, mandatory=True)
        #self.active = self._checkArgAndAssign('active', bool, False, requestObject)
        self.arguments = self._checkArgAndAssign('arguments', str, '', requestObject)
        self.command = self._checkArgAndAssign('command', str, '', requestObject)
        #self.repeat = self._checkArgAndAssign('repeat', bool, False, requestObject)
        #self.repeat_sleep = self._checkArgAndAssign('repeat_sleep', int, 1, requestObject)

        # try to suggest a command if the corresponding 
        # argument was not provided. If this is not possible
        # a ValueError will be raised.
        if self.command == '':
            self._suggestStartCommand()
        
        # create a start command object which will be passed 
        # directly into the process call
        self.startCommandObject = [self.command, self.target_path, self.arguments]
        
        # process architecture
        # self.process = Process(target=self._workload)
        self.subprocess = None
    
    def isAlive (self):

        '''
        A public alias of _subprocessIsAlive.
        The general isAlive response depends fully on the subprocess status.
        '''
        return self._subprocessIsAlive()

    def start (self):

        '''
        Invokes the job.
        '''

        self.subprocess = Popen(self.startCommandObject, stdout=PIPE, stderr=PIPE)
        #print(f'subprocess {self.id} initiated ...')    
        #self.process.start()
        print(f'subprocess {self.id} initiated ...') 

    def stop (self):

        '''
        Stops main- and subprocess immediately.
        '''

        # stop the outer loop first to prevent a repeating inner subprocess
        #self.process.terminate()

        # terminate the subprocess as well
        try:
            while self._subprocessIsAlive():
                self.subprocess.kill()
                sleep(.5)
        except:
            print_exc()
        # finally:  
        #     # flip the active switch
        #     if not self._subprocessIsAlive():
        #         self.active = False

    # - private methods
    def _await (self, subprocess):

        '''
        Blocks an asynchronous subprocess.
        This method simulates the async await context.
        '''

        subprocess.communicate()

    def _checkArgAndAssign (self, arg, argType, expected, requestObject, mandatory=False):

        '''
        Simple routine to check if an argument was provided correctly.
        '''
        if arg in requestObject and type(requestObject[arg]) == argType:
            return requestObject[arg]
        else:
            if mandatory:
                raise ValueError(f'{arg} not specified correctly, {arg} must be a {argType} type.')
            return expected

    def _subprocessIsAlive (self):

        '''
        Returns a boolean based on the subprocess status.
        '''

        return self.subprocess.poll() == None
    
    def _suggestStartCommand (self):

        '''
        Suggests a start command based on file extension
        in provided target path otherwise raises an error.
        '''

        if self.command == '':
            if '.py' in self.target_path:
                self.command= 'python3'
            elif '.sh' in self.target_path:
                self.command = 'bash'
            elif '.js' in self.target_path:
                self.command = 'node'
            elif '.go' in self.target_path:
                self.command = 'go run'
            else:
                raise ValueError(f'Could not determine a suitable command for this {self.target_path}!')
      

class pipe(threading.Thread):

    def __init__(self, function, wait, *args):
        self.wait = wait
        threading.Thread.__init__(self)
        self.func = function
        self.args = args
        self.stoprequest = threading.Event()

    def run(self):
        while not self.stoprequest.isSet():
            try: # important during init, otherwise crash
                self.func(*self.args)
                sleep(self.wait)
            except:
                pass

    def stop(self, timeout = None):
        self.stoprequest.set()
        super(pipe, self).join(timeout)

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

        # managing daemon
        self.daemon = pipe(self._manage, wait=.1)
        self.daemon.start()
        self.log('Started job management daemon.')
    
    def list_to_console (self):

        '''
        A dashboard-like summary output of all deployed jobs.
        '''

        print('job\t\tactive\t\tdisabled\tcreated\t\t\tjob id')
        for id, job in self.jobs.items():
            a_col = '\033[92m'
            if not job["active"]: 
                a_col = '\033[91m'
            print(f'{job["name"]}\t\t{a_col}{job["active"]}\033[0m\t\t{job["disabled"]}\t\t{job["time_created"]}\t{id}')

    def log (self, stdout, color='', indent=0, end='\n'):

        '''
        A simple logger method which allows to direct all outputs to console, file etc.
        '''

        color = color.lower()

        if indent > 0:
            head = ''
            indent = ''.join(['\t']*indent)
        else:
            head = f'\033[96m[ {self.name} | {self._generateUTCTimestamp()} ]\033[0m\t'
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
        # create a dedicated job id
        job_id = self._generateJobId()
        # pass the id to the request object
        # so that the Job object can use it
        # via the request object.
        requestObject['id'] = job_id
        # denote creation time
        time_created = self._generateUTCTimestamp()
        # create a process object
        job_object = Job(requestObject)

        # append new job to jobs object
        self.jobs[job_id] = {
            "active": active,
            "disabled": disable,
            "finished": False,
            "id": job_id,
            "job": job_object,
            "name": requestObject['name'],
            "operating_time_window": operating_time_window,                 
            "operating_week_days": operating_week_days,
            "repeat": True,
            "repeat_sleep": 0,
            "target_path": requestObject['target_path'],
            "time_created": time_created,
            "time_started": None,
            "time_stopped": None
        }

        return True, stdout

    # - private methods
    def _activateIfDeactivated (self, id):

        job = self.jobs[id]

        if not job['active']:
            job['active'] = True
            job['finished'] = False
            job['job'].start()
    
    def _deactivateIfActive (self, id):

        job = self.jobs[id]

        if job['active']:
            job['active'] = False
            self.log(f'Terminating job {id} ...', end='\r')
            job['job'].stop()
            self.log(f'Successfully terminated {id}.\n', 'green', end='\r')

    def _generateJobId (self):
        
        '''
        Generates a new job id.
        The job id is a randomly generated and unique 8 Byte string i.e 16 hex values.
        '''
        
        while True:
            # 8 bytes seed
            byte_seed = randint(0, 255, 8)
            job_id = ''.join(''.join([hex(b) for b in byte_seed]).split('0x'))
            if job_id not in self.jobs:
                return job_id

    def _generateUTCTimestamp (self):

        return datetime.today().strftime("%m-%d-%Y %H:%M:%S")

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

            # override the current activity variable
            # by measuring if the subprocess is alive.
            # This ensures that isAlive() method will not be called inflationary.
            job['active'] = job['job'].isAlive()

            # skip this job if it is disabled on purpose,
            # also make sure everything is deactivated.
            if job['disabled']:
                self._deactivateIfActive(id)
                pass

            # check for weekday and skip if the current day is not included
            if job["operating_week_days"] != 'all' and week_day not in job["operating_week_days"]:
                self._deactivateIfActive(id)
                pass

            # check for time
            if current_hour < int(job["operating_time_window"][0].split(':')[0]) or current_hour > int(job["operating_time_window"][1].split(':')[0]):
                self._deactivateIfActive(id)
                pass
            if current_minute < int(job["operating_time_window"][0].split(':')[1]) or current_minute > int(job["operating_time_window"][1].split(':')[1]):
                self._deactivateIfActive(id)
                pass

            # make sure that the job is finished in case
            # that the job should not be repeated.
            if not job['finished']:
                self._activateIfDeactivated(id)
            if not job['repeat'] and not job['finished']:
                job['finished'] = True

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
        # double loads turns to dict type, 
        # this dictionary will be the extracted request object
        jsonPkg = json.loads(self.rfile.read(int(self.headers['Content-Length'])).decode('utf-8'))
        requestObject = json.loads(jsonPkg) 

        # determine request type
        #   - request: will add a request object
        #   - ls: list all jobs with info
        if requestObject['request'].lower() == 'ls':
            self.Core.list_to_console()
        elif requestObject['request'].lower() == 'job':
            self.Core.log(f"New job request submitted ...", 'y')
            try:
                success, info = self.Core.newJob(requestObject)
                if success:
                    self.Core.log(f"Successfully added new cron job process '{requestObject['name']}'", 'y')
                else:
                    self.Core.log(info, 'red')
            except:
                self.Core.log('An exception occured with the request from', 'red')
                self.Core.log(format_exc(), 'red')        
        


if __name__ == '__main__':
    PORT = 3000
    with http.server.HTTPServer(('localhost', PORT), APIHandler) as srv:
        srv.serve_forever()