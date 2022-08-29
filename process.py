
from subprocess import Popen, PIPE
from multiprocessing import Process
from time import sleep
from traceback import print_exc

target_path = 'test_job.py'
command = 'python3'
arguments = ''
loop = False

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
        self.subprocess = None
        #self.process = Process(target=self._workload)

    def isAlive (self):
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
        
    # def _workload (self):

    #     '''
    #     Repetitive workload piped to a new shell.
    #     Every subprocess is kept persistent for communication.
    #     '''

    #     # print(f'subprocess {self.id} initiated ...')
    #     # self.subprocess = Popen([self.command, self.target_path, self.arguments], stdout=PIPE, stderr=PIPE)
            

    #     while self.active: 

    #         # create a subprocess
    #         print(f'subprocess {self.id} initiated ...')
    #         self.subprocess = Popen([self.command, self.target_path, self.arguments], stdout=PIPE, stderr=PIPE)
            
    #         #block while process is still alive
    #         self._await(self.subprocess)

    #         if not self.repeat:
    #             break
            
    #         while True:
    #             if not self._subprocessIsAlive():
    #                 break
    #             sleep(.2)
    #         sleep(self.repeat_sleep)
        
if __name__ == '__main__':


    jobRequest = {
        'id': 'id0x837h38', # mocked
        'target_path': 'test_job.py'
    }
    j = Job(jobRequest)
    j.start()
    sleep(4)
    print('alive', j._subprocessIsAlive())
    j.stop()
    #sleep(4)
    print('stopped', not j._subprocessIsAlive())
    sleep(10)