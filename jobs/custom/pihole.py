#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
from subprocess import PIPE, STDOUT

class CustomJob:

    '''
    Custom job object to start pihole service.
    '''

    name = 'pihole'
    active = True

    def dependecyCheck (self):
        '''
        This method should return a boolean dep. if the package is installed.
        '''
        
        try:
            readOut = self._cmd('pihole')
            print('readOut', readOut)
            if 'not found' in readOut:
                return False
            else:
                return True
        except:
            return False

    def dependencyInstall (self):
        '''
        This function should install the package.
        Returns a boolean dep. on install success.
        '''
        pass
    
    def isAlive(self):
        '''
        Checks if the process is running.
        '''
        if 'enabled' in self._cmd('pihole status'):
            return True
        return False

    def start (self):
        '''
        A simple method which starts the job.
        '''
        self._cmd('pihole enable')

    def stop (self):
        '''
        Stops the job.
        '''
        self._cmd('pihole disable')
    
    def _cmd (self, command):

        '''
        Runs a commands and returns the stdout.
        '''

        return subprocess.Popen(command, stdout=PIPE, stderr=STDOUT).stdout.readline().decode('utf-8')

cj = custom_job()
print(cj.dependecyCheck())