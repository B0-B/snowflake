#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import pathlib
from os import set_blocking, path, listdir
from cgitb import reset
import threading
from subprocess import Popen, PIPE, STDOUT
from datetime import datetime, timedelta
from numpy.random import randint
from traceback import format_exc, print_exc
from time import sleep
import binascii
from importlib import import_module
import importlib.util
import http.server, cgi
import json

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
            except:
                print_exc()
            finally:
                sleep(self.wait)

    def stop(self, timeout = None):
        self.stoprequest.set()
        super(pipe, self).join(timeout)

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

    def output (self):

        '''
        A function which redirects the stdout from subprocess.
        The console output will be joined to a string and returned.
        '''

        out = {'stdout': '', 'stderr': ''}
        if self.subprocess:
            # print('hit 1')
            # sleep(3)
            # stdout = self.subprocess.stdout
            
            # for line in self.subprocess.stdout:
            #     sys.stdout.write(line)
            #     print(line)
            # print('stdout', stdout)
            # stderr = self.subprocess.stderr.readline().rstrip()
            # print('hit 2')

            # ----- code which extracts the stdout ----
            stdout = ''
            stderr = ''
            # -----------------------------------------
            
            out['stdout'] = stdout#.decode('UTF-8')
            out['stderr'] = stderr#.decode('UTF-8')
            return out
        return out

    def start (self):

        '''
        Invokes the job.
        '''

        if self._subprocessIsAlive():
            print(f'subprocess {self.id} is already alive!')
            return
        self.subprocess = Popen(self.startCommandObject, stdout=PIPE, stderr=STDOUT)
        # disable blocking when trying to communicate with subprocess
        # proposal: https://stackoverflow.com/questions/375427/a-non-blocking-read-on-a-subprocess-pipe-in-python
        set_blocking(self.subprocess.stdout.fileno(), False)
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

    def _exceptionOccured (self):

        '''
        Checks if the subprocess indicates errors/exceptions.
        '''

        return len(self.output()['stderr']) > 0

    def _subprocessIsAlive (self):

        '''
        Returns a boolean based on the subprocess status.
        '''

        if self.subprocess == None:
            return False
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

        # time format
        self.timeFormat = "%m-%d-%Y %H:%M:%S"

        # show banner
        self.log(self.banner, 'blue')

        # process data
        self.jobs = {}

        # API and request parameters
        self.mandatory_parameters = ['name', 'target_path', 'command']

        # load all custom job objects
        self.customDirectory = str(pathlib.Path(__file__).parent.resolve()) + '/jobs/custom'
        self._loadCustomJobs()

        # managing daemon
        # testing = False
        self.counter=0
        # if testing:
        #     while True:
        #         self._manage()
        #         sleep(1)
        # else:
        self.daemon = pipe(self._manage, wait=1)
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
    
    def deploy (self, requestObject):

        '''
        Creates a new entry in jobs object and adds a new job by provided variables.

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
        # override name if it exists
        if 'name' in requestObject:
            name = self._suggestAllowedName(requestObject['name'])
        else:
            name = self._suggestAllowedName('Job')


        # create a dedicated job id
        job_id = self._generateJobId()
        # pass the id to the request object
        # so that the Job object can use it
        # via the request object.
        requestObject['id'] = job_id
        # denote creation time
        time_created = self._generateUTCTimestamp()
        # create a process object (will run internal type tests)
        job_object = Job(requestObject)
        

        # append new job to jobs object
        self.jobs[job_id] = {
            "active": active,
            "disabled": disable,
            "finished": False,
            "id": job_id,
            "job": job_object,
            "name": name,
            "operating_time_window": operating_time_window,                 
            "operating_week_days": operating_week_days,
            "repeat": repeat,
            "repeat_sleep": 0,
            "target_path": requestObject['target_path'],
            "time_created": time_created,
            "time_duration": 0,
            "time_started": None,
            "time_stopped": None
        }

        return True, stdout

    def disable (self, identifier):

        '''
        Enables a job which corresponds with the identifier.
        The identifier can be the job id or name.
        '''

        self._enableJob(identifier, False)
        
    def enable (self, identifier):

        '''
        Disables a job which corresponds with the identifier.
        The identifier can be the job id or name.
        '''

        self._enableJob(identifier, True)

    # - private methods
    def _activateIfDeactivated (self, id):

        job = self.jobs[id]

        if not job['active']:
            self.log(f'Starting job {id} ...', 'y', end='\r')
            job['active'] = True
            # every outside/external activation call 
            # will reset the finished argument
            job['finished'] = False
            # denote the start time
            job['time_started'] = self._generateUTCTimestamp()
            # finally start the job workload
            job['job'].start()
            
    def _deactivateIfActive (self, id):

        job = self.jobs[id]

        if job['active']:
            self.log(f'Terminating job {id} ...', end='\r')
            job['active'] = False
            job['job'].stop()
            
            job['time_stopped'] = self._generateUTCTimestamp()
            delta = datetime.strptime(job['time_stopped'], self.timeFormat) - datetime.strptime(job['time_started'], self.timeFormat)
            # denote the time duration and save in job object
            job['time_duration'] = delta.strftime("%d days %H:%M:%S")
            self.log(f'Successfully terminated {id} after {job["time_duration"]} duration. \n', 'green', end='\r')

    def _enableJob (self, identifier, value):

        '''
        Enables or disables the job corresponding to the provided
        identifier. If the value provided is True, job will be enabled,
        and vice versa.
        '''

        # find the corresponding job
        job = None
        if identifier in self.jobs:
            job = self.jobs[identifier]
        else:
            for j in self.jobs.values():
                if j['name'] == identifier:
                    job = j
        
        # check if a job could be found
        if not job:
            self.log(f"No job was found for identifier '{identifier}'", 'red')
        else:
            job['disabled'] = not value
            if value:
                self.log(f"Successfully enabled '{job['name']}' ({job['id']}).", 'green')
            else:
                self.log(f"Successfully disabled '{job['name']}' ({job['id']}).", 'blue')

    def _findIdByName (self, name):

        job = self._findJobByName(name)
        if job:
            return job['id']
        return None

    def _findJobByName (self, name):

        '''
        Returns a job if the name matched the filter
        otherwise it returns None.
        '''

        for job in self.jobs.values():
            if name == job['name']:
                return job
        return None

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

        return datetime.today().strftime(self.timeFormat)

    def _loadCustomJobs (self):

        '''
        Submethod which imports all custom job objects and deploys them.
        '''

        self.log(f'Load custom jobs from  {self.customDirectory} ...')

        # load all file names
        for file in listdir(self.customDirectory):
            # check if the parsed node is a file
            isFile = pathlib.Path(self.customDirectory+'/'+file).is_file()
            if isFile and 'template' not in file and '__init__' not in file:
                # override module string in relative python
                # path fashion, so it is parsed correctly by importlib
                module = f"jobs.custom.{file.replace('.py', '')}"
                # try to import
                try:
                    # extract job object from the module
                    spec = importlib.util.spec_from_file_location(module, self.customDirectory+'/'+file)
                    custom_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(custom_module)
                    job = custom_module.CustomJob()
                    # check before deploy if the dependecies are met
                    if not job.dependencyCheck():
                        self.log(f"No dependencies installed for custom job {module}, skip deployment ...", 'y')
                        continue
                    # ----- deploying -----
                    # now an alternative deploy is performed
                    # for this generate an id and name first
                    job_id = self._generateJobId()
                    name = self._suggestAllowedName(job.name)
                    # for custom jobs there is no targetpath needed, since the
                    # workload is triggered directly from the custom job object (method).
                    # The target_path will be overriden with the path of the custom job file.
                    target_path = self.customDirectory+'/'+file
                    # deploy the job by appending the new job to the jobs object
                    self.jobs[job_id] = {
                        "active": job.active,
                        "disabled": False,
                        "finished": False,
                        "id": job_id,
                        "job": job,
                        "name": name,
                        "operating_time_window": None,                 
                        "operating_week_days": 'all',
                        "repeat": False,
                        "repeat_sleep": 0,
                        "target_path": target_path,
                        "time_created": self._generateUTCTimestamp(),
                        "time_duration": 0,
                        "time_started": None,
                        "time_stopped": None
                    }
                    self.log(f"Successfully deployed custom job '{name}'", 'blue')
                except:
                    self.log(f"Could not import custom job '{module}'\n{format_exc()}", 'red')

    def _manage (self):
        
        '''
        An automatic steering algorithm.
        The pipe respects the active variable in the job object only if the job is not disabled
        and will flip it according to the time operating window.
        '''

        try:
            current_hour = datetime.now().hour
            current_minute = datetime.now().minute
            week_day = datetime.today().strftime('%A').lower()[:3]
            for id in self.jobs.keys():
                # override the current activity variable
                # by measuring if the subprocess is alive.
                # This ensures that isAlive() method will not be called inflationary.
                job = self.jobs[id]
                job['active'] = job['job'].isAlive()
                # skip this job if it is disabled on purpose,
                # also make sure everything is deactivated.
                if job['disabled']:
                    self._deactivateIfActive(id)
                    continue
                # check for weekday and skip if the current day is not included
                if job["operating_week_days"] != 'all' and week_day not in job["operating_week_days"]:
                    self._deactivateIfActive(id)
                    continue
                # check for time
                if job["operating_time_window"]:
                    if current_hour < int(job["operating_time_window"][0].split(':')[0]) or current_hour > int(job["operating_time_window"][1].split(':')[0]):
                        self._deactivateIfActive(id)
                        continue
                    if current_minute < int(job["operating_time_window"][0].split(':')[1]) or current_minute > int(job["operating_time_window"][1].split(':')[1]):
                        self._deactivateIfActive(id)
                        continue
                # make sure that the job is finished in case
                # that the job should not be repeated.
                if not job['active'] and not job['finished']:
                    # activate the job if it's not actively running
                    # and the finished flag was not enabled.
                    self._activateIfDeactivated(id)
                    if not job['repeat']:
                        # set the finished flag to true already
                        # to avoid another trigger in the next round
                        job['finished'] = True
                        # check if errors or exceptions might have
                        # caused the job to finish.
                        if job['job']._exceptionOccured():
                            self.log(f"Job '{job['name']}' ({id}) finished due to errors:", 'red')
                            self.log(job['job'].output()['stderr'], 'red', indent=1)
                        else:
                            self.log(f"Job '{job['name']}' ({id}) finished successfully.", 'green')
        except:
            self.log(format_exc(), 'red')

    def _suggestAllowedName (self, name):

        '''
        Checks if a name exists already in the jobs object to ensure bijective mapping.
        If a job is already named by e.g. 'process' and a suggestion for the word 
        'process' is requested, the function will return 'process_1'.
        Further calls will produce 'process_2', 'process_3' and so on.
        '''

        name_copy = name
        while name_copy in self.jobs:
            try:
                # check if an integer was appended already at the end
                last_id = int(name_copy.split('_')[-1])
                
                # new id is generated by incrementation of the last id
                id = last_id + 1

                # build new name 
                name_copy = name_copy.split('_')
                name_copy[-1] = id
                name_copy = ''.join(name_copy)
            except:
                name_copy = name_copy + '_1'
            
        return name_copy

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
        # double loads() turns to dict type, 
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
                self.Core.list_to_console()
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

            elif requestObject['request'].lower() == 'set':
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
            


if __name__ == '__main__':
    PORT = 3000
    with http.server.HTTPServer(('localhost', PORT), APIHandler) as srv:
        srv.serve_forever()