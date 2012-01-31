# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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

"""
mod_python's apache module remapping
"""

class SERVER_RETURN(Exception):
    pass

class CookieError(Exception):
    pass

## Some constants

HTTP_CONTINUE                     = 100
HTTP_SWITCHING_PROTOCOLS          = 101
HTTP_PROCESSING                   = 102
HTTP_OK                           = 200
HTTP_CREATED                      = 201
HTTP_ACCEPTED                     = 202
HTTP_NON_AUTHORITATIVE            = 203
HTTP_NO_CONTENT                   = 204
HTTP_RESET_CONTENT                = 205
HTTP_PARTIAL_CONTENT              = 206
HTTP_MULTI_STATUS                 = 207
HTTP_MULTIPLE_CHOICES             = 300
HTTP_MOVED_PERMANENTLY            = 301
HTTP_MOVED_TEMPORARILY            = 302
HTTP_SEE_OTHER                    = 303
HTTP_NOT_MODIFIED                 = 304
HTTP_USE_PROXY                    = 305
HTTP_TEMPORARY_REDIRECT           = 307
HTTP_BAD_REQUEST                  = 400
HTTP_UNAUTHORIZED                 = 401
HTTP_PAYMENT_REQUIRED             = 402
HTTP_FORBIDDEN                    = 403
HTTP_NOT_FOUND                    = 404
HTTP_METHOD_NOT_ALLOWED           = 405
HTTP_NOT_ACCEPTABLE               = 406
HTTP_PROXY_AUTHENTICATION_REQUIRED = 407
HTTP_REQUEST_TIME_OUT             = 408
HTTP_CONFLICT                     = 409
HTTP_GONE                         = 410
HTTP_LENGTH_REQUIRED              = 411
HTTP_PRECONDITION_FAILED          = 412
HTTP_REQUEST_ENTITY_TOO_LARGE     = 413
HTTP_REQUEST_URI_TOO_LARGE        = 414
HTTP_UNSUPPORTED_MEDIA_TYPE       = 415
HTTP_RANGE_NOT_SATISFIABLE        = 416
HTTP_EXPECTATION_FAILED           = 417
HTTP_UNPROCESSABLE_ENTITY         = 422
HTTP_LOCKED                       = 423
HTTP_FAILED_DEPENDENCY            = 424
HTTP_UPGRADE_REQUIRED             = 426
HTTP_INTERNAL_SERVER_ERROR        = 500
HTTP_NOT_IMPLEMENTED              = 501
HTTP_BAD_GATEWAY                  = 502
HTTP_SERVICE_UNAVAILABLE          = 503
HTTP_GATEWAY_TIME_OUT             = 504
HTTP_VERSION_NOT_SUPPORTED        = 505
HTTP_VARIANT_ALSO_VARIES          = 506
HTTP_INSUFFICIENT_STORAGE         = 507
HTTP_NOT_EXTENDED                 = 510

# The APLOG constants in Apache are derived from syslog.h
# constants, so we do same here.

try:
    import syslog
    APLOG_EMERG = syslog.LOG_EMERG     # system is unusable
    APLOG_ALERT = syslog.LOG_ALERT     # action must be taken immediately
    APLOG_CRIT = syslog.LOG_CRIT       # critical conditions
    APLOG_ERR = syslog.LOG_ERR         # error conditions
    APLOG_WARNING = syslog.LOG_WARNING # warning conditions
    APLOG_NOTICE = syslog.LOG_NOTICE   # normal but significant condition
    APLOG_INFO = syslog.LOG_INFO       # informational
    APLOG_DEBUG = syslog.LOG_DEBUG     # debug-level messages
except ImportError:
    APLOG_EMERG = 0
    APLOG_ALERT = 1
    APLOG_CRIT = 2
    APLOG_ERR = 3
    APLOG_WARNING = 4
    APLOG_NOTICE = 5
    APLOG_INFO = 6
    APLOG_DEBUG = 7

APLOG_NOERRNO = 8

OK = REQ_PROCEED = 0
DONE = -2
DECLINED = REQ_NOACTION = -1

_status_values = {
    "postreadrequesthandler":   [ DECLINED, OK ],
    "transhandler":             [ DECLINED ],
    "maptostoragehandler":      [ DECLINED ],
    "inithandler":              [ DECLINED, OK ],
    "headerparserhandler":      [ DECLINED, OK ],
    "accesshandler":            [ DECLINED, OK ],
    "authenhandler":            [ DECLINED ],
    "authzhandler":             [ DECLINED ],
    "typehandler":              [ DECLINED ],
    "fixuphandler":             [ DECLINED, OK ],
    "loghandler":               [ DECLINED, OK ],
    "handler":                  [ OK ],
}

# constants for get_remote_host
REMOTE_HOST = 0
REMOTE_NAME = 1
REMOTE_NOLOOKUP = 2
REMOTE_DOUBLE_REV = 3

# legacy/mod_python things
REQ_ABORTED = HTTP_INTERNAL_SERVER_ERROR
REQ_EXIT = "REQ_EXIT"
PROG_TRACEBACK = "PROG_TRACEBACK"

# the req.finfo tuple
FINFO_MODE = 0
FINFO_INO = 1
FINFO_DEV = 2
FINFO_NLINK = 3
FINFO_UID = 4
FINFO_GID = 5
FINFO_SIZE = 6
FINFO_ATIME = 7
FINFO_MTIME = 8
FINFO_CTIME = 9
FINFO_FNAME = 10
FINFO_NAME = 11
FINFO_FILETYPE = 12

# the req.parsed_uri
URI_SCHEME = 0
URI_HOSTINFO = 1
URI_USER = 2
URI_PASSWORD = 3
URI_HOSTNAME = 4
URI_PORT = 5
URI_PATH = 6
URI_QUERY = 7
URI_FRAGMENT = 8

# for req.proxyreq
PROXYREQ_NONE = 0       # No proxy
PROXYREQ_PROXY = 1      # Standard proxy
PROXYREQ_REVERSE = 2    # Reverse proxy
PROXYREQ_RESPONSE = 3   # Origin response

# methods for req.allow_method()
M_GET = 0               # RFC 2616: HTTP
M_PUT = 1
M_POST = 2
M_DELETE = 3
M_CONNECT = 4
M_OPTIONS = 5
M_TRACE = 6             # RFC 2616: HTTP
M_PATCH = 7
M_PROPFIND = 8          # RFC 2518: WebDAV
M_PROPPATCH = 9
M_MKCOL = 10
M_COPY = 11
M_MOVE = 12
M_LOCK = 13
M_UNLOCK = 14           # RFC2518: WebDAV
M_VERSION_CONTROL = 15  # RFC3253: WebDAV Versioning
M_CHECKOUT = 16
M_UNCHECKOUT = 17
M_CHECKIN = 18
M_UPDATE = 19
M_LABEL = 20
M_REPORT = 21
M_MKWORKSPACE = 22
M_MKACTIVITY = 23
M_BASELINE_CONTROL = 24
M_MERGE = 25
M_INVALID = 26           # RFC3253: WebDAV Versioning

# for req.used_path_info
AP_REQ_ACCEPT_PATH_INFO = 0  # Accept request given path_info
AP_REQ_REJECT_PATH_INFO = 1  # Send 404 error if path_info was given
AP_REQ_DEFAULT_PATH_INFO = 2 # Module's choice for handling path_info


# for mpm_query
AP_MPMQ_NOT_SUPPORTED      = 0  # This value specifies whether
                                # an MPM is capable of
                                # threading or forking.
AP_MPMQ_STATIC             = 1  # This value specifies whether
                                # an MPM is using a static # of
                                # threads or daemons.
AP_MPMQ_DYNAMIC            = 2  # This value specifies whether
                                # an MPM is using a dynamic # of
                                # threads or daemons.

AP_MPMQ_MAX_DAEMON_USED    = 1  # Max # of daemons used so far
AP_MPMQ_IS_THREADED        = 2  # MPM can do threading
AP_MPMQ_IS_FORKED          = 3  # MPM can do forking
AP_MPMQ_HARD_LIMIT_DAEMONS = 4  # The compiled max # daemons
AP_MPMQ_HARD_LIMIT_THREADS = 5  # The compiled max # threads
AP_MPMQ_MAX_THREADS        = 6  # # of threads/child by config
AP_MPMQ_MIN_SPARE_DAEMONS  = 7  # Min # of spare daemons
AP_MPMQ_MIN_SPARE_THREADS  = 8  # Min # of spare threads
AP_MPMQ_MAX_SPARE_DAEMONS  = 9  # Max # of spare daemons
AP_MPMQ_MAX_SPARE_THREADS  = 10 # Max # of spare threads
AP_MPMQ_MAX_REQUESTS_DAEMON= 11 # Max # of requests per daemon
AP_MPMQ_MAX_DAEMONS        = 12 # Max # of daemons by config

# magic mime types
CGI_MAGIC_TYPE = "application/x-httpd-cgi"
INCLUDES_MAGIC_TYPE = "text/x-server-parsed-html"
INCLUDES_MAGIC_TYPE3 = "text/x-server-parsed-html3"
DIR_MAGIC_TYPE = "httpd/unix-directory"

# for req.read_body
REQUEST_NO_BODY = 0
REQUEST_CHUNKED_ERROR = 1
REQUEST_CHUNKED_DECHUNK = 2

""" Constants not defined (need _apache import)

# for req.connection.keepalive
AP_CONN_UNKNOWN = _apache.AP_CONN_UNKNOWN
AP_CONN_CLOSE = _apache.AP_CONN_CLOSE
AP_CONN_KEEPALIVE = _apache.AP_CONN_KEEPALIVE

# for req.finfo[apache.FINFO_FILETYPE]
APR_NOFILE = _apache.APR_NOFILE
APR_REG = _apache.APR_REG
APR_DIR = _apache.APR_DIR
APR_CHR = _apache.APR_CHR
APR_BLK = _apache.APR_BLK
APR_PIPE = _apache.APR_PIPE
APR_LNK = _apache.APR_LNK
APR_SOCK = _apache.APR_SOCK
APR_UNKFILE = _apache.APR_UNKFILE
"""

# for apache.stat()
APR_FINFO_LINK = 0x00000001 # Stat the link not the file itself if it is a link
APR_FINFO_MTIME = 0x00000010 # Modification Time
APR_FINFO_CTIME = 0x00000020 # Creation or inode-changed time
APR_FINFO_ATIME = 0x00000040 # Access Time
APR_FINFO_SIZE = 0x00000100 # Size of the file
APR_FINFO_CSIZE = 0x00000200 # Storage size consumed by the file
APR_FINFO_DEV = 0x00001000 # Device
APR_FINFO_INODE = 0x00002000 # Inode
APR_FINFO_NLINK = 0x00004000 # Number of links
APR_FINFO_TYPE = 0x00008000 # Type
APR_FINFO_USER = 0x00010000 # User
APR_FINFO_GROUP = 0x00020000 # Group
APR_FINFO_UPROT = 0x00100000 # User protection bits
APR_FINFO_GPROT = 0x00200000 # Group protection bits
APR_FINFO_WPROT = 0x00400000 # World protection bits
APR_FINFO_ICASE = 0x01000000 # if dev is case insensitive
APR_FINFO_NAME = 0x02000000 # ->name in proper case
APR_FINFO_MIN = 0x00008170 # type, mtime, ctime, atime, size
APR_FINFO_IDENT = 0x00003000 # dev and inode
APR_FINFO_OWNER = 0x00030000 # user and group
APR_FINFO_PROT = 0x00700000 # all protections
APR_FINFO_NORM = 0x0073b170 # an atomic unix apr_stat()
APR_FINFO_DIRENT = 0x02000000 # an atomic unix apr_dir_read()


HTTP_STATUS_MAP = {
    100: "Continue",
    101: "Switching Protocols",
    200: "OK",
    201: "Created",
    202: "Accepted",
    203: "Non-Authoritative Information",
    204: "No Content",
    205: "Reset Content",
    206: "Partial Content",
    300: "Multiple Choices",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    305: "Use Proxy",
    307: "Temporary Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    407: "Proxy Authentication Required",
    408: "Request Time-out",
    4090: "Conflict",
    4101: "Gone",
    4112: "Length Required",
    4123: "Precondition Failed",
    4134: "Request Entity Too Large",
    4145: "Request-URI Too Large",
    4156: "Unsupported Media Type",
    4167: "Requested range not satisfiable",
    4178: "Expectation Failed",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Time-out",
    505: "HTTP Version not supported",
}
