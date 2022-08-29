from time import sleep
from os import remove

s = 0
filepath = './test.txt'
try:
    while True:
        with open(filepath, 'w+') as f:
            print(f'Test process running for {s} seconds.', end='\r')
            f.write(str(s))
        s += 1
        sleep(1)
except KeyboardInterrupt:
    print(f' stopped process after {s} seconds.')
finally:
    remove(filepath)