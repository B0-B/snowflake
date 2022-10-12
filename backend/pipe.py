#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
from traceback import print_exc
from time import sleep

class pipe(threading.Thread):

    '''
    Thread pipe.
    '''

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
