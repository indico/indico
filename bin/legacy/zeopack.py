# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

#!python
"""Connect to a ZEO server and ask it to pack.

Usage: zeopack.py [options]

Options:

    -p port -- port to connect to

    -h host -- host to connect to (default is current host)

    -U path -- Unix-domain socket to connect to

    -S name -- storage name (default is '1')

    -d days -- pack objects more than days old

    -1 -- Connect to a ZEO 1 server

    -W -- wait for server to come up.  Normally the script tries to
       connect for 10 seconds, then exits with an error.  The -W
       option is only supported with ZEO 1.

You must specify either -p and -h or -U.
"""

import getopt
import socket
import sys
import time

from ZEO.ClientStorage import ClientStorage

WAIT = 10 # wait no more than 10 seconds for client to connect

def connect(storage):
    # The connect-on-startup logic that ZEO provides isn't too useful
    # for this script.  We'd like to client to attempt to startup, but
    # fail if it can't get through to the server after a reasonable
    # amount of time.  There's no external support for this, so we'll
    # expose the ZEO 1.0 internals.  (consenting adults only)
    t0 = time.time()
    while t0 + WAIT > time.time():
        storage._call.connect()
        if storage._connected:
            return
    raise RuntimeError, "Unable to connect to ZEO server"

def pack1(addr, storage, days, wait):
    cs = ClientStorage(addr, storage=storage,
                       wait_for_server_on_startup=wait)
    if wait:
        # _startup() is an artifact of the way ZEO 1.0 works.  The
        # ClientStorage doesn't get fully initialized until registerDB()
        # is called.  The only thing we care about, though, is that
        # registerDB() calls _startup().
        cs._startup()
    else:
        connect(cs)
    cs.invalidator = None
    cs.pack(wait=1, days=days)
    cs.close()

def pack2(addr, storage, days):
    cs = ClientStorage(addr, storage=storage, wait=1, read_only=1)
    cs.pack(wait=1, days=days)
    cs.close()

def usage(exit=1):
    print __doc__
    print " ".join(sys.argv)
    sys.exit(exit)

def main():
    host = None
    port = None
    unix = None
    storage = '1'
    days = 0
    wait = 0
    zeoversion = 2
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'p:h:U:S:d:W1')
        for o, a in opts:
            if o == '-p':
                port = int(a)
            elif o == '-h':
                host = a
            elif o == '-U':
                unix = a
            elif o == '-S':
                storage = a
            elif o == '-d':
                days = int(a)
            elif o == '-W':
                wait = 1
            elif o == '-1':
                zeoversion = 1
    except Exception, err:
        print err
        usage()

    if unix is not None:
        addr = unix
    else:
        if host is None:
            host = socket.gethostname()
        if port is None:
            usage()
        addr = host, port

    if zeoversion == 1:
        pack1(addr, storage, days, wait)
    else:
        pack2(addr, storage, days)

if __name__ == "__main__":
    try:
        main()
    except Exception, err:
        print err
        sys.exit(1)
