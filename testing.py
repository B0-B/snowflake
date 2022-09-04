from client import client
from time import sleep
'''
0 deploy test
1 list jobs info
2 disable job
'''



c = client()

def test(test_id):

    if test_id == 0:
        r = 'deploy'
        jobRequest = {
            'request': r,
            'name': 'testing',
            'target_path': '/home/b1/snowflake/test_job.py',
            'command': 'python3'
        }
    elif test_id == 1:
        r = 'ls'
        jobRequest = {
            'request': 'ls'
        }
    elif test_id == 2:
        jobRequest = {
            'request': 'disable',
            'name': 'testing'
        }
    print(c.post(jobRequest))


test(0) # deploy
#quit()
sleep(3)
test(1) # check status
sleep(3)
test(2) # disable
sleep(1)
test(1) # check status