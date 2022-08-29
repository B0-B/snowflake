from time import sleep

s = 0
try:
    while True:
        print(f'Test process running for {s} seconds.', end='\r')
        s += 1
        sleep(1)
except KeyboardInterrupt:
    print(f' stopped process after {s} seconds.')