#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

class CustomJob:

    '''
    Custom job object to start system services.
    '''

    def dependecyCheck (self):
        '''
        This method should return a boolean dep. if the package is installed.
        '''
        return True

    def dependencyInstall (self):
        '''
        This function should install the package.
        Returns a boolean dep. on install success.
        '''
        return True
    
    def isAlive(self):
        '''
        Checks if the process is running.
        '''
        command = 'check command'
        readOut = os.popen(command).read()

    def start (self):
        '''
        A simple method which starts the job.
        '''
        os.system('start command')

    def stop (self):
        '''
        Stops the job.
        '''
        os.system('stop command')
    
    def _cmd (self, command):

        '''
        Runs a commands and returns the stdout.
        '''

        return subprocess.Popen(command, stdout=PIPE, stderr=STDOUT).stdout.readline().decode('utf-8')