import PyKCS11
import threading
import fcntl
import time
import struct
import sys
import os
import logging
import ConfigParser
import binascii

# Defaults for the program constants, DO NOT change them here, insert your own
# values in /etc/token-tools.conf
tokenrng_defaults = {'pkcs11_library': '/usr/lib/opensc-pkcs11.so',
                        'reader_slot': '0',
                  'random_chunk_size': '128',
                      'entropy_ratio': '2',
                              'debug': 'no'}

tokenrng_config = ConfigParser.ConfigParser(defaults=tokenrng_defaults)
tokenrng_config.read('/etc/token-tools.conf')


""" 
    constants

"""

FS_DEV_RANDOM = '/dev/random'
PROC_ENTROPY_AVAIL = '/proc/sys/kernel/random/entropy_avail'

DEBUG = tokenrng_config.getboolean('Global', 'debug')

# The actual PKCS#11 library on the system used to interact with your
# cryptographic token, defaults to OpenSC
PKCS11_LIBRARY = tokenrng_config.get('Global', 'pkcs11_library')

# Which reader slot is the token connected to, should be zero when only one
# token is ever connected
READER_SLOT = tokenrng_config.getint('Global', 'reader_slot')

# How much random data to request from the library in each pass
RANDOM_CHUNK_SIZE = tokenrng_config.getint('Global', 'random_chunk_size')

# Depending on the device + PKCS#11 library, the actual entropy per byte
# received may be less than 8bits per byte, so we must make it configurable by
# the user. Defaults low at 2bits per byte, increase if you're SURE your
# device+library provide more. 
ENTROPY_RATIO = tokenrng_config.getint('Global', 'entropy_ratio')


# This IOCTL macro was derived from include/uapi/linux/random.h in linux source
RNDADDENTROPY = 1074287107
# It seems to be universally constant, but in case it isn't, we could retrieve
# it from the kernel headers on each system at runtime and fall back to this one
# if they're missing. To check, compile and run this C on your Linux system:
# gcc -o randaddentropy randaddentropy.c; ./randaddentropy
"""
#include <linux/random.h>
#include <stdio.h>

int main(void) {
    int rndval = RNDADDENTROPY;
    printf("\n RNDADDENTROPY: %d", rndval);
    return 0;
}
"""



"""
    globals
    
"""

pkcs11_api = None
token_session = None

# Someday we'll handle signals or other runtime commands but for now just loop
RUN_LOOP = True


# setup logging according to configuration
log = logging.getLogger(__name__)
if DEBUG:
    log.setLevel(logging.DEBUG)
else:
    log.setLevel(logging.INFO)
mainHandler = logging.StreamHandler()
mainHandler.setFormatter(logging.Formatter('%(levelname)s %(asctime)s - %(module)s - %(funcName)s: %(message)s'))
log.addHandler(mainHandler)


# helper functions
def pkcs11_getrandom():
    if token_session is not None:
        raw = token_session.generateRandom(RANDOM_CHUNK_SIZE)
        rand_byte_array = bytearray(raw)
        rand_byte_hex = binascii.hexlify(rand_byte_array)
        log.debug('Random data length: %d bytes, hex value: %s' % (len(rand_byte_array),rand_byte_hex))
        return rand_byte_array
    else:
        log.error('No token session available, can\'t get random data')
        return None
        
def pkcs11_reset(library=None):
    global pkcs11_api
    global token_session
    if library is not None:
        log.debug('Initializing library: %s' % library)
        pkcs11_api = PyKCS11.PyKCS11Lib()
        pkcs11_api.load(library)
        while token_session is None:
            try:
                token_session = pkcs11_api.openSession(READER_SLOT)
                log.debug('Token session initialized: %s' % token_session)
            except PyKCS11.PyKCS11Error as e:
                token_session = None
                log.error('Token session unavailable at slot: %s, check configuration', READER_SLOT)
            time.sleep(3)

def print_entropy_avail():
    with open(PROC_ENTROPY_AVAIL, 'r') as entropy_avail:
        log.debug('Entropy in pool: %s' % entropy_avail.readline())


# main program loop
def run_loop():
    log.info('TokenRNG initializing at %s', time.ctime())
    log.debug('Config defaults: %s', tokenrng_config.defaults())
    log.debug('Config token: %s', tokenrng_config.items('Global'))
    try:
        while RUN_LOOP:
            if token_session is None:
                pkcs11_reset(library=PKCS11_LIBRARY)
            random_sample = pkcs11_getrandom()
            if random_sample is not None:
                fmt = 'ii%is' % RANDOM_CHUNK_SIZE
                packed_data = struct.pack(fmt,
                                          len(random_sample) * ENTROPY_RATIO,
                                          len(random_sample),
                                          str(random_sample))
                with open(FS_DEV_RANDOM, 'a+') as dev_random:
                    fcntl.ioctl(dev_random, RNDADDENTROPY, packed_data)
                print_entropy_avail()
            time.sleep(1)
    except KeyboardInterrupt as e:
        log.debug('Exiting due to keyboard interrupt')
        sys.exit(0)


if __name__ == '__main__':
    run_loop()
        

