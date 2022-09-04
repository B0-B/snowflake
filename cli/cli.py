#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
A client-side command line interface implementation for snowflake.
Requests are sent exclusively via http requests to the snowflake socket.
________________________________________________________________________

[Usage]

    The general usage pattern is
        sf command [--optional-args]
    for instance: 
        sf set --host
'''

# _________________ Define CLI Commands _________________
__commands__ = [
    ('set', 'Change snowflake hostname/IP or port settings.'), 
    ('ping', 'Ping snowflake server. Demands no arguments.'), 
    ('deploy', 'Deploy program or package remotely. Demands other optional arguments: --name, --target_path, etc.'), 
    ('config', 'Configure a job. Demands optional arguments: --id or --name (identifier), --arg tuple.'), 
    ('ls', 'Outputs status monitor for all jobs. Demands no arguments.'), 
    ('enable', 'Enables a (apriori deployed) job. Demands optional arguments: --id or --name (identifier).'), 
    ('disable', 'Disables a deployed job. Demands optional arguments: --id or --name (identifier).'),
    ('halt', 'Disables all services immediately. Demands no arguments.')
]

# ______________ Define Optional Arguments ______________
__optional__ = {
    'id': ('--id', 'Specify job name as identifier.', str),
    'name': ('--name', 'Specify job name as identifier.', str),
    'arg': ('--arg', 'Specify a job argument, e.g. --arg=("active", True)', tuple),
    'host': ('--host', 'Sets/overrides hostname or ip of snowflake server.', str), 
    'port': ('--port', 'Sets/overrides hostname or ip of snowflake server.', str), 
    'target_path': ('--target_path', 'Set the target path of the program/script/file for the job.', str), 
    'weekdays': ('--weekdays', 'Limit the job service to specific weekdays, provide a string of days sep. by a "," e.g.\nmon,tue,wed,saturday. The service will only be active on the provided days.', str), 
    'daytime': ('--daytime', 'Limit the job service to specific time window during the day. Provide a string of accending times in 0-23 hour format sep. by a "," e.g.\n12:00,12:30. The service will only be active during the provided window.', str), 
    'repeat': ('--repeat', 'Whether the job should repeat once it has finished.', bool),
}

__command_args__ = {
    'set': ['host', 'port'],
    'ping': [],
    'config': ['arg'],
    'deploy': ['target_path', 'weekdays', 'daytime', 'repeat'],
    'ls': ['id', 'name'],
    'enable': ['id', 'name'],
    'disable': ['id', 'name'],
    'halt': []
}


import argparse
import json
from traceback import format_exc
import requests
import pathlib

__alias__ = 'sf'
__root__ = str(pathlib.Path(__file__).parent.resolve())
__json__ = __root__ + '/server.json'
 
def log (stdout, color='', indent=0, end='\n'):

    '''
    A simple logger method which allows to direct all outputs to console, file etc.
    '''

    if indent > 0:
        indent = ''.join(['\t']*indent)
    else:
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
    
    print(f'{indent}{color}{stdout}\033[0m', end=end)

def post (url, options):

    '''
    Simple socket post method.
    '''

    try:
        response = requests.post(url, json=json.dumps(options))
        response.encoding = response.apparent_encoding
        response = json.loads(response.text)
        if len(response['errors']) > 0:
            log(response['errors'][0], 'red')
        else:
            log(response['response'][0])
    except:
        log(format_exc(), 'red')

if __name__ == '__main__':


    # inititalize argument parser
    description = 'A client-side command line interface implementation for snowflake.\nFor more information please visit: https://github.com/B0-B/snowflake'
    parser = argparse.ArgumentParser(prog=__alias__, description=description)

    for arg, info in __optional__.items():
        parser.add_argument(info[0], help=info[1], type=info[2])
        #command_group.add_argument(option[0], help=option[1])
    
    # add command arguments
    subparsers = parser.add_subparsers(help='Required CLI command option.')
    subparsers_dict = {}
    #command_group = parser.add_argument_group('Command', 'Required CLI command option.')
    for option in __commands__:
        command, help = option
        subparsers_dict[command] = subparsers.add_parser(command, help=help)
        subparser = subparsers_dict[command]
    # add optional arguments
    

    # add optional arguments
    # add command arguments
    # option_group = parser.add_argument_group('Opt. Arguments', 'Required CLI command option.')
    # for arg in __optional__:
    #     option_group.add_argument(arg[0], default=arg[2], help=arg[1], required=False)

    # first parse all arguments, this assures that when initialized
    # the warning can be skipped.
    args = parser.parse_args()

    # parse server json for context
    with open(__json__) as f:
        server_json = json.load(f)
        host = server_json['host']
        port = server_json['port']
        if 'http://' not in host:
            host = 'http://' + host
        url = host + ':' + str(port)

    # check if a host was provided otherwise warn,
    # but first check a priori if a host was just set,
    # then the warning may be skipped.
    print('test', args.__dict__['host'])
    if 'host' in args.__dict__ and args.__dict__['host'] != None:
        host = args.__dict__['host']
        if 'http://' not in host:
            host = 'http://' + host
        url = host + ':' + str(port)
        try:
            if post(url, {'request': 'ping'}) != 'ok':
                ValueError()
            with open(__json__, "w+") as f:
                json.dump(f)
            log('Successfully reached snowflake server and set new host.', 'green')
        except:
            log(f'Cannot reach server under {url}', 'red')
            quit() 
    if host in ['', 'http://']: # check if host variable is still empty
        log(f'WARNING: No host name provided yet!\nPlease set the hostname or host IP e.g. \n"{__alias__} set --host=raspberry or \n"{__alias__} set --host=192.168.1.2"', 'y')
        quit()
    else: 
        try:
            if post(url, {'request': 'ping'}) != 'ok':
                ValueError()
        except:
            log(f'Cannot reach server under {url}', 'red')
            quit() 

    # parse the raw input command word by word
    rawInputWords = []
    for word in args.text.split(' '):
        if word != '':
            rawInputWords.append(word)

    # next parse the command from the raw input 
    # which is crucial to continue
    command = rawInputWords[1]
    if command not in __commands__:
        log(f"'{command}' is not a valid command. See valid commands with '{__alias__} --help'.", 'red')
        quit()
    
    # -- ls
    if command == 'ls':
        log(post(url, {'request': 'ls'}))
    elif command == 'set':
        log('Successfully set server information.')
