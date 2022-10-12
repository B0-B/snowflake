#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from backend.pipe import pipe
import pathlib
from os import listdir
from datetime import datetime
from numpy.random import randint
from traceback import format_exc
import importlib.util

class Core:

    '''
    A shell level interface to an http.server-compliant cron-job handler.
    Schedules, deploys and monitors jobs with quick access into the process. 
    '''

    banner=f'''
        
    s n o w f l a k e

         🄯 {min([2022, datetime.now().year])} 
    '''

    name = 'snowflake'

    def __init__ (self):

        # time format
        self.timeFormat = "%m-%d-%Y %H:%M:%S"

        # show banner
        self.log(self.banner, 'blue', indent=1)

        # process data
        self.jobs = {}

        # API and request parameters
        self.mandatory_parameters = ['name', 'target_path', 'command']

        # load all custom job objects
        self.customDirectory = str(pathlib.Path(__file__).parent.parent.resolve()) + '/jobs/custom'
        self._loadCustomJobs()

        # ping response
        self.ping_response = 'ping received.'

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
        self.log('Started job management.')
    
    def list_to_console (self):

        '''
        A dashboard-like summary output of all deployed jobs.
        '''

        print(self._list())

    def log (self, stdout, color='', indent=0, end='\n', no_stamp=False):

        '''
        A simple logger method which allows to direct all outputs to console, file etc.
        '''

        if indent > 0 or no_stamp:
            stamp = ''
            indent = ''.join(['\t']*indent)
        else:
            stamp = f'\033[96m[ {self.name} | {self._generateUTCTimestamp()} ]\033[0m\t'
            indent = ''
        color = color.lower()
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
        
        print(f'{stamp}{indent}{color}{stdout}\033[0m', end=end)
    
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
            job['time_duration'] = delta
            
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

    def _list (self):

        '''
        Lists all jobs to a string table.
        '''

        output = 'job\t\tactive\t\tdisabled\tcreated\t\t\tjob id'
        for id, job in self.jobs.items():
            a_col = '\033[92m'
            if not job["active"]: 
                a_col = '\033[91m'
            output += f'\n{job["name"]}\t\t{a_col}{job["active"]}\033[0m\t\t{job["disabled"]}\t\t{job["time_created"]}\t{id}'
        return output

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

    def _retrieveServerInfoFrom (self, handler):

        '''
        This method is called in the handler.
        '''
        print('hello')

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
