#!/usr/bin/env python3
import time
import sys
import logging

logger = logging.getLogger("test")
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(logging.StreamHandler(sys.stdout))
logger.propagate = False

while True:
    time.sleep(1)    
    #print("IMPORTANT MESSAGE")
    #sys.stderr.write("Ooooops\n")
    #sys.stdout.flush()
    #sys.stderr.flush()
    logger.info("something exciting")
