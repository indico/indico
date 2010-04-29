#!/usr/bin/env python2.3

##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

"""Simple consistency checker for FileStorage.

usage: fstest.py [-v] data.fs

The fstest tool will scan all the data in a FileStorage and report an
error if it finds any corrupt transaction data.  The tool will print a
message when the first error is detected, then exit.

The tool accepts one or more -v arguments.  If a single -v is used, it
will print a line of text for each transaction record it encounters.
If two -v arguments are used, it will also print a line of text for
each object.  The objects for a transaction will be printed before the
transaction itself.

Note: It does not check the consistency of the object pickles.  It is
possible for the damage to occur only in the part of the file that
stores object pickles.  Those errors will go undetected.
"""

# The implementation is based closely on the read_index() function in
# ZODB.FileStorage.  If anything about the FileStorage layout changes,
# this file will need to be udpated.

import string
import struct
import sys

class FormatError(ValueError):
    """There is a problem with the format of the FileStorage."""

class Status:
    checkpoint = 'c'
    undone = 'u'

packed_version = 'FS21'

TREC_HDR_LEN = 23
DREC_HDR_LEN = 42

VERBOSE = 0

def hexify(s):
    """Format an 8-bite string as hex"""
    l = []
    for c in s:
        h = hex(ord(c))
        if h[:2] == '0x':
            h = h[2:]
        if len(h) == 1:
            l.append("0")
        l.append(h)
    return "0x" + string.join(l, '')

def chatter(msg, level=1):
    if VERBOSE >= level:
        sys.stdout.write(msg)

def U64(v):
    """Unpack an 8-byte string as a 64-bit long"""
    h, l = struct.unpack(">II", v)
    if h:
        return (h << 32) + l
    else:
        return l

def check(path):
    file = open(path, 'rb')

    file.seek(0, 2)
    file_size = file.tell()
    if file_size == 0:
        raise FormatError("empty file")
    file.seek(0)
    if file.read(4) != packed_version:
        raise FormatError("invalid file header")

    pos = 4L
    tid = '\000' * 8 # lowest possible tid to start
    i = 0
    while pos:
        _pos = pos
        pos, tid = check_trec(path, file, pos, tid, file_size)
        if tid is not None:
            chatter("%10d: transaction tid %s #%d \n" %
                    (_pos, hexify(tid), i))
            i = i + 1


def check_trec(path, file, pos, ltid, file_size):
    """Read an individual transaction record from file.

    Returns the pos of the next transaction and the transaction id.
    It also leaves the file pointer set to pos.  The path argument is
    used for generating error messages.
    """

    h = file.read(TREC_HDR_LEN)
    if not h:
        return None, None
    if len(h) != TREC_HDR_LEN:
        raise FormatError("%s truncated at %s" % (path, pos))

    tid, stl, status, ul, dl, el = struct.unpack(">8s8scHHH", h)
    tmeta_len = TREC_HDR_LEN + ul + dl + el

    if tid <= ltid:
        raise FormatError("%s time-stamp reduction at %s: %s <= %s" %
                          (path, pos, hexify(tid), hexify(ltid)))
    ltid = tid

    tl = U64(stl) # transaction record length - 8
    if pos + tl + 8 > file_size:
        raise FormatError("%s truncated possibly because of"
                          " damaged records at %s" % (path, pos))
    if status == Status.checkpoint:
        raise FormatError("%s checkpoint flag was not cleared at %s"
                          % (path, pos))
    if status not in ' up':
        raise FormatError("%s has invalid status '%s' at %s" %
                          (path, status, pos))

    if tmeta_len > tl:
        raise FormatError("%s has an invalid transaction header"
                          " at %s" % (path, pos))

    tpos = pos
    tend = tpos + tl

    if status != Status.undone:
        pos = tpos + tmeta_len
        file.read(ul + dl + el) # skip transaction metadata

        i = 0
        while pos < tend:
            _pos = pos
            pos, oid = check_drec(path, file, pos, tpos, tid)
            if pos > tend:
                raise FormatError("%s has data records that extend beyond"
                                  " the transaction record; end at %s" %
                                  (path, pos))
            chatter("%10d: object oid %s #%d\n" % (_pos, hexify(oid), i),
                    level=2)
            i = i + 1

    file.seek(tend)
    rtl = file.read(8)
    if rtl != stl:
        raise FormatError("%s has inconsistent transaction length"
                          " for undone transaction at %s" % (path, pos))
    pos = tend + 8
    return pos, tid

def check_drec(path, file, pos, tpos, tid):
    """Check a data record for the current transaction record"""

    h = file.read(DREC_HDR_LEN)
    if len(h) != DREC_HDR_LEN:
        raise FormatError("%s truncated at %s" % (path, pos))
    oid, serial, _prev, _tloc, vlen, _plen = (
        struct.unpack(">8s8s8s8sH8s", h))
    prev = U64(_prev)
    tloc = U64(_tloc)
    plen = U64(_plen)
    dlen = DREC_HDR_LEN + (plen or 8)

    if vlen:
        dlen = dlen + 16 + vlen
        file.seek(8, 1)
        pv = U64(file.read(8))
        file.seek(vlen, 1) # skip the version data

    if tloc != tpos:
        raise FormatError("%s data record exceeds transaction record "
                          "at %s: tloc %d != tpos %d" %
                          (path, pos, tloc, tpos))

    pos = pos + dlen
    if plen:
        file.seek(plen, 1)
    else:
        file.seek(8, 1)
        # _loadBack() ?

    return pos, oid

def usage():
    print __doc__
    sys.exit(-1)

def main():
    import getopt

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'v')
        if len(args) != 1:
            raise ValueError("expected one argument")
        for k, v in opts:
            if k == '-v':
                global VERBOSE
                VERBOSE = VERBOSE + 1
    except (getopt.error, ValueError):
        usage()

    try:
        check(args[0])
    except FormatError, msg:
        print msg
        sys.exit(-1)

    chatter("no errors detected")

if __name__ == "__main__":
    main()

