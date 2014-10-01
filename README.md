#TokenTools

TokenTools is a set of simple utilities for interacting with cryptographic tokens like smartcards, hardware security modules (HSMs) and other similar devices.

TokenTools is a successor project to a program I wrote a few years ago called CardRand, which I am [deprecating](#deprecating-cardrand) in favor of something cleaner, more capable and reliable.

##TokenRNG

The first addition to TokenTools is TokenRNG,  a direct replacement for CardRand. Instead of using libopensc directly as CardRand did, TokenRNG uses the standard PKCS#11 interface, so any device that is supported by a PKCS#11 library should work, including all devices that work with OpenSC as they provide a PKCS#11 library.

###Security notes

It is possible that your cryptographic token is not actually giving you good
quality random data, and it is also possible that your PKCS#11 library is altering
what the token provides. All TokenRNG can do is make it possible to use them as
a kernel entropy source, trust and entropy quality decisions are up to you.

By default, TokenRNG tells the kernel that there are only 2 bits of entropy per 
byte of data received from the PKCS#11 library (the entropy_ratio configuration
setting). This is probably a sane default in most cases. Setting it to zero will
still mix random data from your device into the kernel pool without increasing
the entropy count. Setting it to 8 is probably unwise without a very good reason.


###Setup

Before you try to use anything in TokenTools, you need to ensure you have a working cryptographic token with all the right drivers and libraries installed. Some minor assistance to help you with that is available in the [Token Support](#token-support) section.

Very minimal setup is required to use TokenRNG from the git repository, but you do need to install any libraries required to support your cryptographic token, and one Python library which can be installed either from your Linux package manager or from PyPi into a virtualenv.

Package names and instructions are written for Ubuntu/Debian, so minor changes may be needed for Arch, Suse, CentOS, Fedora and others.

####Clone the repo

At some point I may upload TokenTools to PyPi or package it for specific Linux distributions, but for now it's all just in git, so you'll just need to clone the repo to the right spot.

    cd /opt/
    git clone https://github.com/infincia/TokenTools.git

####Install Python libraries

If you intend to use a virtualenv, create and activate it, then install the python libraries into it:

    virtualenv /opt/TokenTools/env
    source /opt/TokenTools/env/bin/activate
    pip install -r /opt/TokenTools/requirements.txt

If you don't intend to use a virtualenv, just install the PyKCS11 library directly from your package manager:

    sudo aptitude install python-pykcs11
    
####Configuration

There's a simple, optional configuration file included in the root of the project called 'token-tools.conf.sample'. If you need to change the configuration for any of the utilities in TokenTools, copy and rename that file to '/etc/token-tools.conf':

    cp /opt/TokenTools/token-tools.conf.sample /etc/token-tools.conf

If no configuration file is present in '/etc/', TokenRNG will simply use sane default settings that will work for most situations.
 
###Using TokenRNG

As long as your token is generally working on the system, TokenRNG should work fine. You may need to change the 'reader_slot' configuration option in '/etc/token-tools.conf' if your token isn't in slot 0.

If you leave the token plugged in all the time and aren't using it for anything else it, TokenRNG should work all the time without issue.

####Run TokenRNG directly for testing
    
If using a virtualenv, first activate it:

    source /opt/TokenTools/env/bin/activate

Then run the program directly to test it:

    cd /opt/TokenTools
    python token-rng.py


####Long term use

There are 2 Ubuntu Upstart scripts included in the repo, just copy one of them to /etc/init and Upstart will keep it running for you.

If you're using a virtualenv:

    cp /opt/TokenTools/token-rng.upstart-virtualenv /etc/init/token-rng.conf
    service token-rng start
    
Otherwise:

    cp /opt/TokenTools/token-rng.upstart-systempy /etc/init/token-rng.conf
    service token-rng start


##Token Support

You'll  need a working PKCS#11 library and drivers for your token, and you'll need to ensure you can use the token on the system before trying to get TokenTools to work with it.

There are some tokens that just work 100% with OpenSC, and others that don't work without proprietary drivers from the manufacturer even if they are CCID compliant, even on Linux, so you'll need to obtain those. 

I believe 'pcscd' and/or 'pcsclite' need to be installed for all of them, so do that first:

    sudo aptitude install pcscd libpcsclite1 pcsc-tools

###OpenSC supported tokens

Install the right components directly from your Linux packager manager

    sudo aptitude install openct opensc  
    
###Safenet/Aladdin eTokens

The eToken PRO 32k, eToken PRO 64k and a few other models *should* work with OpenSC, so try that first. The eToken PRO 72K Javacard model and some of the other newer models require the proprietary Safenet Authentication Client in order to work on Linux. You'll have to find SAC via Google as it isn't freely available. The most recent version I'm aware of is SAC 8.3, but I don't have it and I'm currently using SAC 8.1 on Ubuntu 13.04 without much trouble.

For SAC 8.1 I needed to install libhal1 and create some symlinks before everything worked:

    apt-get install libhal1
    dpkg -i SafenetAuthenticationClient-8.1.0-5_amd64.deb
    ln -s /lib64/libeToken.so.8.1 /usr/lib64/eToken/libeToken.so.8
    ln -s /lib64/libeTokenUI.so.8.1 /usr/lib64/eToken/libeTokenUI.so.8
    
###Testing your token

Plug in your token and run one of these:

    opensc-tool -l
    openct-tool list
    pcsc_scan
     
If your token shows up with any of those commands, you shouldn't have much trouble getting it to work with TokenTools. If nothing shows up, 'pcscd' or 'openct' or a proprietary service for your token may need to be running, check the documentation for it.

##Deprecating CardRand

CardRand was a simple C program that used the hardware random number generator (HWRNG) present in many smartcard/eToken devices as a random number source for the Linux kernel entropy pool, allowing systems that don't otherwise have a high quality HWRNG built-in to attach one easily, even on systems like laptops or embedded ARM devices where connecting a PCI card or making internal modifications is not possible. Only a USB port on the host and a USB cryptographic token are required in most cases, which are both very common.

Back when it was written, CardRand worked pretty well for the quick hack that it was. However, it was designed to use OpenSC libraries directly, which prevented it from working with any cryptographic tokens that OpenSC did not support.

Additionally, the functions CardRand was using in libopensc were likely never intended to be used by other applications at all, but rather were used to support their own internal tools like opensc-explorer. So the functions CardRand depended on were something of a defacto "private API", and they do seem to have changed more than once from one OpenSC release to another.

There's a better way to do this.

So, CardRand is deprecated. It does not work on most systems anymore, it is difficult to compile with modern versions of OpenSC on modern Linux distributions, and TokenRNG is a superior drop-in replacement for it.

