# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import time
import random
import os
import base64
import binascii

from mimetypes import MimeTypes
from indico.web.wsgi import webinterface_handler_config as apache
from indico.web.wsgi.webinterface_handler_config import \
    SERVER_RETURN, HTTP_NOT_FOUND

_mimes = MimeTypes(strict=False)
_mimes.suffix_map.update({'.tbz2' : '.tar.bz2'})
_mimes.encodings_map.update({'.bz2' : 'bzip2'})

def stream_file(req, fullpath, fullname=None, mime=None, encoding=None, etag=None, md5=None, location=None):
    """This is a generic function to stream a file to the user.
    If fullname, mime, encoding, and location are not provided they will be
    guessed based on req and fullpath.
    md5 should be passed as an hexadecimal string.
    """
    def normal_streaming(size):
        req.set_content_length(size)
        req.send_http_header()
        if not req.header_only:
            req.sendfile(fullpath)
        return ""

    def single_range(size, the_range):
        req.set_content_length(the_range[1])
        req.headers_out['Content-Range'] = 'bytes %d-%d/%d' % (the_range[0], the_range[0] + the_range[1] - 1, size)
        req.status = apache.HTTP_PARTIAL_CONTENT
        req.send_http_header()
        if not req.header_only:
            req.sendfile(fullpath, the_range[0], the_range[1])
        return ""

    def multiple_ranges(size, ranges, mime):
        req.status = apache.HTTP_PARTIAL_CONTENT
        boundary = '%s%04d' % (time.strftime('THIS_STRING_SEPARATES_%Y%m%d%H%M%S'), random.randint(0, 9999))
        req.content_type = 'multipart/byteranges; boundary=%s' % boundary
        content_length = 0
        for arange in ranges:
            content_length += len('--%s\r\n' % boundary)
            content_length += len('Content-Type: %s\r\n' % mime)
            content_length += len('Content-Range: bytes %d-%d/%d\r\n' % (arange[0], arange[0] + arange[1] - 1, size))
            content_length += len('\r\n')
            content_length += arange[1]
            content_length += len('\r\n')
        content_length += len('--%s--\r\n' % boundary)
        req.set_content_length(content_length)
        req.send_http_header()
        if not req.header_only:
            for arange in ranges:
                req.write('--%s\r\n' % boundary, 0)
                req.write('Content-Type: %s\r\n' % mime, 0)
                req.write('Content-Range: bytes %d-%d/%d\r\n' % (arange[0], arange[0] + arange[1] - 1, size), 0)
                req.write('\r\n', 0)
                req.sendfile(fullpath, arange[0], arange[1])
                req.write('\r\n', 0)
            req.write('--%s--\r\n' % boundary)
            req.flush()
        return ""

    def parse_date(date):
        """According to <http://www.w3.org/Protocols/rfc2616/rfc2616-sec3.html#sec3.3>
        a date can come in three formats (in order of preference):
            Sun, 06 Nov 1994 08:49:37 GMT  ; RFC 822, updated by RFC 1123
            Sunday, 06-Nov-94 08:49:37 GMT ; RFC 850, obsoleted by RFC 1036
            Sun Nov  6 08:49:37 1994       ; ANSI C's asctime() format
        Moreover IE is adding some trailing information after a ';'.
        Wrong dates should be simpled ignored.
        This function return the time in seconds since the epoch GMT or None
        in case of errors."""
        if not date:
            return None
        try:
            date = date.split(';')[0].strip() # Because of IE
            ## Sun, 06 Nov 1994 08:49:37 GMT
            return time.mktime(time.strptime(date, '%a, %d %b %Y %X %Z'))
        except:
            try:
                ## Sun, 06 Nov 1994 08:49:37 GMT
                return time.mktime(time.strptime(date, '%A, %d-%b-%y %H:%M:%S %Z'))
            except:
                try:
                    ## Sun, 06 Nov 1994 08:49:37 GMT
                    return time.mktime(date)
                except:
                    return None

    def parse_ranges(ranges):
        """According to <http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.35>
        a (multiple) range request comes in the form:
            bytes=20-30,40-60,70-,-80
        with the meaning:
            from byte to 20 to 30 inclusive (11 bytes)
            from byte to 40 to 60 inclusive (21 bytes)
            from byte 70 to (size - 1) inclusive (size - 70 bytes)
            from byte size - 80 to (size - 1) inclusive (80 bytes)
        This function will return the list of ranges in the form:
            [[first_byte, last_byte], ...]
        If first_byte or last_byte aren't specified they'll be set to None
        If the list is not well formatted it will return None
        """
        try:
            if ranges.startswith('bytes') and '=' in ranges:
                ranges = ranges.split('=')[1].strip()
            else:
                return None
            ret = []
            for arange in ranges.split(','):
                arange = arange.strip()
                if arange.startswith('-'):
                    ret.append([None, int(arange[1:])])
                elif arange.endswith('-'):
                    ret.append([int(arange[:-1]), None])
                else:
                    ret.append(map(int, arange.split('-')))
            return ret
        except:
            return None

    def parse_tags(tags):
        """Return a list of tags starting from a comma separated list."""
        return [tag.strip() for tag in tags.split(',')]

    def fix_ranges(ranges, size):
        """Complementary to parse_ranges it will transform all the ranges
        into (first_byte, length), adjusting all the value based on the
        actual size provided.
        """
        ret = []
        for arange in ranges:
            if (arange[0] is None and arange[1] > 0) or arange[0] < size:
                if arange[0] is None:
                    arange[0] = size - arange[1]
                elif arange[1] is None:
                    arange[1] = size - arange[0]
                else:
                    arange[1] = arange[1] - arange[0] + 1
                arange[0] = max(0, arange[0])
                arange[1] = min(size - arange[0], arange[1])
                if arange[1] > 0:
                    ret.append(arange)
        return ret

    def get_normalized_headers(headers):
        """Strip and lowerize all the keys of the headers dictionary plus
        strip, lowerize and transform known headers value into their value."""
        ret = {
            'if-match' : None,
            'unless-modified-since' : None,
            'if-modified-since' : None,
            'range' : None,
            'if-range' : None,
            'if-none-match' : None,
        }
        for key, value in req.headers_in.iteritems():
            key = key.strip().lower()
            value = value.strip()
            if key in ('unless-modified-since', 'if-modified-since'):
                value = parse_date(value)
            elif key == 'range':
                value = parse_ranges(value)
            elif key == 'if-range':
                value = parse_date(value) or parse_tags(value)
            elif key in ('if-match', 'if-none-match'):
                value = parse_tags(value)
            if value:
                ret[key] = value
        return ret

    if UseXSendFile:
        ## If XSendFile is supported by the server, let's use it.
        if os.path.exists(fullpath):
            if fullname is None:
                fullname = os.path.basename(fullpath)
            req.headers_out["Content-Disposition"] = 'inline; filename="%s"' % fullname.replace('"', '\\"')
            req.headers_out["X-Sendfile"] = fullpath
            if mime is None:
                (mime, encoding) = _mimes.guess_type(fullpath)
                if mime is None:
                    mime = "application/octet-stream"
            req.content_type = mime
            return ""
        else:
            raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND

    headers = get_normalized_headers(req.headers_in)
    if headers['if-match']:
        if etag is not None and etag not in headers['if-match']:
            raise apache.SERVER_RETURN, apache.HTTP_PRECONDITION_FAILED

    if os.path.exists(fullpath):
        mtime = os.path.getmtime(fullpath)
        if fullname is None:
            fullname = os.path.basename(fullpath)
        if mime is None:
            (mime, encoding) = _mimes.guess_type(fullpath)
            if mime is None:
                mime = "application/octet-stream"
        if location is None:
            location = req.uri
        req.content_type = mime
        req.encoding = encoding
        req.filename = fullname
        req.headers_out["Last-Modified"] = time.strftime('%a, %d %b %Y %X GMT', time.gmtime(mtime))
        req.headers_out["Accept-Ranges"] = "bytes"
        req.headers_out["Content-Location"] = location
        if etag is not None:
            req.headers_out["ETag"] = etag
        if md5 is not None:
            req.headers_out["Content-MD5"] = base64.encodestring(binascii.unhexlify(md5.upper()))[:-1]
        req.headers_out["Content-Disposition"] = 'inline; filename="%s"' % fullname.replace('"', '\\"')
        size = os.path.getsize(fullpath)
        if not size:
            try:
                raise Exception, '%s exists but is empty' % fullpath
            except Exception:
                raise SERVER_RETURN, HTTP_NOT_FOUND
            raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND
        if headers['if-modified-since'] and headers['if-modified-since'] >= mtime:
            raise apache.SERVER_RETURN, apache.HTTP_NOT_MODIFIED
        if headers['if-none-match']:
            if etag is not None and etag in headers['if-none-match']:
                raise apache.SERVER_RETURN, apache.HTTP_NOT_MODIFIED
        if headers['unless-modified-since'] and headers['unless-modified-since'] < mtime:
            return normal_streaming(size)
        if headers['range']:
            try:
                if headers['if-range']:
                    if etag is None or etag not in headers['if-range']:
                        return normal_streaming(size)
                ranges = fix_ranges(headers['range'], size)
            except:
                return normal_streaming(size)
            if len(ranges) > 1:
                return multiple_ranges(size, ranges, mime)
            elif ranges:
                return single_range(size, ranges[0])
            else:
                raise apache.SERVER_RETURN, apache.HTTP_RANGE_NOT_SATISFIABLE
        else:
            return normal_streaming(size)
    else:
        raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND

UseXSendFile = False
