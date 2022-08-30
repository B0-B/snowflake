from client import client

'''
0 deploy test
1 list jobs info
2 disable job
'''

test_id = 0  

if test_id == 0:

    c = client()
    r = 'deploy'
    #r = 'ls'
    jobRequest = {
        'request': r,
        'name': 'test',
        'target_path': '~/snowflake/test_job.py',
        'command': 'python3'
    }
    c.post(jobRequest)

elif test_id == 1:

    c = client()
    #r = 'deploy'
    r = 'lss'
    jobRequest = {
        'request': r,
        'name': 'test',
        'target_path': '~/snowflake/test_job.py',
        'command': 'python3'
    }
    c.post(jobRequest)

elif test_id == 2:

    c = client()
    jobRequest = {
        'request': 'set',
        'argument': ('disable', True),
        'name': 'test'
    }
    c.post(jobRequest)