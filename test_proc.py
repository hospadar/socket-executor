#!/usr/bin/env python3
import time
import sys
while True:
    time.sleep(1)    
    print("IMPORTANT MESSAGE")
    sys.stderr.write("Ooooops\n")
    sys.stdout.flush()
    sys.stderr.flush()
