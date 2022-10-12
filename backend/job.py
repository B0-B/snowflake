#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import set_blocking
from subprocess import Popen, PIPE, STDOUT
from traceback import print_exc
from time import sleep

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
        self.subprocess = Popen(self.startCommandObject, stdout=PIPE, stderr=STDOUT)
        # disable blocking when trying to communicate with subprocess
        # proposal: https://stackoverflow.com/questions/375427/a-non-blocking-read-on-a-subprocess-pipe-in-python
        set_blocking(self.subprocess.stdout.fileno(), False)

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