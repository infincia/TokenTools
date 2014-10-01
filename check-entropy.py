#!/usr/bin/env python

import sys
import os
import logging
import time

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
mainHandler = logging.StreamHandler()
mainHandler.setFormatter(logging.Formatter('%(levelname)s %(asctime)s - %(module)s - %(funcName)s: %(message)s'))
log.addHandler(mainHandler)


PROC_ENTROPY_AVAIL = '/proc/sys/kernel/random/entropy_avail'


def print_entropy_avail():
    with open(PROC_ENTROPY_AVAIL, 'r') as entropy_avail:
        log.info('Entropy in pool: %s' % entropy_avail.readline())


def run_loop():
    try:
        while True:
            print_entropy_avail()
            time.sleep(1)
    except KeyboardInterrupt as e:
        log.debug('Exiting due to keyboard interrupt')
        sys.exit(0)


if __name__ == '__main__':
    run_loop()