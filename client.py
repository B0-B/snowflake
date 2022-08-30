#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests, urllib.request, json, os
 

class client:

    def __init__ (self, url='localhost', port=3000):

        # create url
        if 'http' not in url: 
            url = 'http://' + url
        self.url = f'{url}:{port}'
    
    def post (self, options):

        response = requests.post(self.url, json=json.dumps(options)) #, cert=(f'{self.certDir}/key.pem', f'{self.certDir}/cert.pem') )
        response.encoding = response.apparent_encoding
        return json.loads(response.text)

    
if __name__ == '__main__':

    c = client()
    #r = 'deploy'
    r = 'ls'
    jobRequest = {
        'request': r,
        'name': 'test',
        'target_path': '~/snowflake/test_job.py',
        'command': 'python3'
    }
    c.post(jobRequest)

    # jobRequest = {
    #     'request': 'ls',
    #     'name': 'test',
    #     'target_path': '~/snowflake/test_job.py',
    #     'command': 'python3',
    #     'arguments': '',
    #     'repeat': False,
    #     'repeat_sleep': False,
    #     'active': False    
    # }
    c.post(jobRequest)