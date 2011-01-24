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

"""
Main wsgi handler

This code has partially been taken from CDS Invenio,
under the corresponding GNU GPL license.
"""

import sys
import os
from types import ClassType

# indico imports
from indico.web.rh import RHHtdocs

# legacy indico imports
from MaKaC.common import Config



# Path update

DIR_HTDOCS = Config.getInstance().getHtdocsDir()
PATH = [os.path.join(DIR_HTDOCS, '../'), \
        DIR_HTDOCS]
for p in PATH:
    if p not in sys.path:
        sys.path.append(p)

###

from wsgiref.util import FileWrapper, guess_scheme

from indico.web.wsgi.webinterface_handler_config import \
     HTTP_STATUS_MAP, SERVER_RETURN, OK, DONE, \
     HTTP_NOT_FOUND, HTTP_INTERNAL_SERVER_ERROR, \
    REMOTE_HOST, REMOTE_NOLOOKUP
from indico.web.wsgi.indico_wsgi_handler_utils import table, FieldStorage, \
     registerException, _check_result
from indico.web.wsgi.indico_wsgi_url_parser import is_mp_legacy_publisher_path

# Legacy imports
from MaKaC.plugins.base import RHMapMemory

if __name__ != "__main__":
    # Chances are that we are inside mod_wsgi.
    # You can't write to stdout in mod_wsgi, but instead to stderr
    sys.stdout = sys.stderr

def application(environ, start_response):
    """
    Entry point for wsgi.
    """
    ## Needed for mod_wsgi
    ## see: <http://code.google.com/p/modwsgi/wiki/ApplicationIssues>
    req = SimulatedModPythonRequest(environ, start_response)

    possible_module, possible_handler = is_mp_legacy_publisher_path(req)

    # The POST form processing has to be done after checking the path
    req.get_post_form()

    try:
        try:
            #if condition:
            #    wsgi_publisher(possible_module, possible_handler)
            if possible_module is not None:
                mp_legacy_publisher(req, possible_module, possible_handler)
            else:
                from indico.web.wsgi.indico_wsgi_file_handler import stream_file

                url = req.URLFields['PATH_INFO']
                possible_static_path = None

                # maybe the url is owned by some plugin?
                pluginRHMap = RHMapMemory()._map

                for urlRE, rh in pluginRHMap.iteritems():
                    m = urlRE.match(url)
                    if m:

                        if type(rh) == ClassType or RHHtdocs not in rh.mro():
                            plugin_publisher(req, url, rh, m.groupdict())
                        else:
                            # calculate the path to the resource
                            possible_static_path = rh.calculatePath(**m.groupdict())

                if not possible_static_path:
                    # Finally, it might be a static file
                    possible_static_path = is_static_path(environ['PATH_INFO'])

                if possible_static_path is not None:
                    stream_file(req, possible_static_path)
                else:
                    raise SERVER_RETURN, HTTP_NOT_FOUND

            req.flush()
        #Exception treatment
        except SERVER_RETURN, status:
            status = int(str(status))
            if status not in (OK, DONE):
                req.status = status
                req.headers_out['content-type'] = 'text/html'
                start_response(req.get_wsgi_status(),
                               req.get_low_level_headers(),
                               sys.exc_info())
                return ('%s' % indicoErrorWebpage(status),)
            else:
                req.flush()
        # If we reach this block, there was probably
        # an error importing a legacy python module
        except Exception:
            req.status = HTTP_INTERNAL_SERVER_ERROR
            req.headers_out['content-type'] = 'text/html'
            start_response(req.get_wsgi_status(),
                           req.get_low_level_headers(),
                           sys.exc_info())
            registerException()
            return ('%s' % indicoErrorWebpage(500),)
    finally:
        for (callback, data) in req.get_cleanups():
            callback(data)
    return []

def indicoErrorWebpage(status):
    """
    Calls the tpl containing the error webpage.
    Returns a string with the error webpage we want to generate.
    """
    from MaKaC.webinterface.pages.error import WErrorWSGI
    from MaKaC.i18n import _
    errorTitleText = (_("Page not found"),
                      _("The page you were looking for doesn't exist."))
    if status != 404:
        errorTitleText = (_("%s" % (HTTP_STATUS_MAP.get(status, "Unknown error"))),
                          "An unexpected error ocurred.")
    wsError = WErrorWSGI(errorTitleText)
    return wsError.getHTML()

def is_static_path(path):
    """
    Returns True if path corresponds to an existing file under DIR_HTDOCS.
    @param path: the path.
    @type path: string
    @return: True if path corresponds to an existing file under DIR_HTDOCS.
    @rtype: bool
    """
    path = os.path.abspath(DIR_HTDOCS + path)
    if path.startswith(DIR_HTDOCS) and os.path.isfile(path):
        return path
    return None

def _convert_to_string(form):
    for key, value in form.items():
        ## FIXME: this is a backward compatibility workaround
        ## because most of the old administration web handler
        ## expect parameters to be of type str.
        ## When legacy publisher will be removed all this
        ## pain will go away anyway :-)
        if isinstance(value, str):
            form[key] = str(value)


def plugin_publisher(req, path, rh, urlparams):
    """
    Publishes the plugin described in path
    """
    form = dict(req.form)

    _convert_to_string(form)
    _check_result(req, rh(req, **urlparams).process( form ))

def mp_legacy_publisher(req, possible_module, possible_handler):
    """
    mod_python legacy publisher minimum implementation.
    """
    the_module = open(possible_module).read()
    module_globals = {}

    try:
        exec(the_module, module_globals)
    except:
        # Log which file caused the exec error (traceback won't do it for
        # some reason) and relaunch the exception
        registerException('Error executing the module %s' % possible_module)
        raise

    if possible_handler in module_globals and \
           callable(module_globals[possible_handler]):
        from indico.web.wsgi.indico_wsgi_handler_utils import _check_result
        ## the req.form must be casted to dict because of Python 2.4 and earlier
        ## otherwise any object exposing the mapping interface can be
        ## used with the magic **
        form = dict(req.form)

        _convert_to_string(form)

        try:
            return _check_result(req, module_globals[possible_handler](req, **form))
        except TypeError, err:
            if ("%s() got an unexpected keyword argument" % possible_handler) in \
                   str(err) or ('%s() takes at least' % possible_handler) in str(err):
                import inspect
                inspected_args = inspect.getargspec(module_globals[possible_handler])
                expected_args = list(inspected_args[0])
                expected_defaults = list(inspected_args[3])
                expected_args.reverse()
                expected_defaults.reverse()
                # Write the exception to Apache error log file
                registerException("Wrong GET parameter set in calling a legacy "
                                  "publisher handler for %s: expected_args=%s, "
                                  "found_args=%s" % \
                                  (possible_handler, repr(expected_args),
                                   repr(req.form.keys())))
                cleaned_form = {}
                for index, arg in enumerate(expected_args):
                    if arg == 'req':
                        continue
                    if index < len(expected_defaults):
                        cleaned_form[arg] = form.get(arg, expected_defaults[index])
                    else:
                        cleaned_form[arg] = form.get(arg, None)
                return _check_result(req,
                                     module_globals[possible_handler](req,
                                                                      **cleaned_form))
            else:
                raise
    else:
        raise SERVER_RETURN, HTTP_NOT_FOUND

class InputProcessed(object):
    """
    Auxiliary class used when reading input.
    @see: <http://www.wsgi.org/wsgi/Specifications/handling_post_forms>.
    """
    def read(self, *args):
        raise EOFError('The wsgi.input stream has already been consumed')
    readline = readlines = __iter__ = read


class SimulatedModPythonRequest(object):
    """
    mod_python like request object.
    Minimum and cleaned implementation to make moving out of mod_python
    easy.
    @see: <http://www.modpython.org/live/current/doc-html/pyapi-mprequest.html>
    """
    def __init__(self, environ, start_response):
        from urllib import quote
        self.__environ = environ
        self.__start_response = start_response
        self.__response_sent_p = False
        self.__buffer = ''
        self.__low_level_headers = []
        self.__headers = table(self.__low_level_headers)
        self.__headers.add = self.__headers.add_header
        self.__status = "200 OK"
        self.__filename = None
        self.__disposition_type = None
        self.__bytes_sent = 0
        self.__allowed_methods = []
        self.__cleanups = []
        self.headers_out = self.__headers
        ## See: <http://www.python.org/dev/peps/pep-0333/#the-write-callable>
        self.__write = None
        self.__errors = environ['wsgi.errors']
        self.__headers_in = table([])
        for key, value in environ.iteritems():
            if key.startswith('HTTP_'):
                self.__headers_in[key[len('HTTP_'):].replace('_', '-')] = value
        if environ.get('CONTENT_LENGTH'):
            self.__headers_in['content-length'] = environ['CONTENT_LENGTH']
        if environ.get('CONTENT_TYPE'):
            self.__headers_in['content-type'] = environ['CONTENT_TYPE']
        ## HTTP headers variables
        ## We might want to add some other fields in the future
        self.URLFields = {'URL_SCHEME':   environ['wsgi.url_scheme'], \
                    'HTTP_HOST':    environ.get('HTTP_HOST', ''), \
                    'SERVER_NAME':  environ.get('SERVER_NAME', ''), \
                    'SERVER_PORT':  environ['SERVER_PORT'], \
                    'SCRIPT_NAME':  quote(environ.get('SCRIPT_NAME', '')), \
                    'PATH_INFO':    quote(environ.get('PATH_INFO','')), \
                    'QUERY_STRING': environ.get('QUERY_STRING', '')}

    def get_wsgi_environ(self):
        return self.__environ

    def get_post_form(self):
        post_form = self.__environ.get('wsgi.post_form')
        input = self.__environ['wsgi.input']
        if (post_form is not None
            and post_form[0] is input):
            return post_form[2]
        # This must be done to avoid a bug in cgi.FieldStorage
        self.__environ.setdefault('QUERY_STRING', '')
        fs = FieldStorage(self, keep_blank_values=1)
        if fs.wsgi_input_consumed:
            new_input = InputProcessed()
            post_form = (new_input, input, fs)
            self.__environ['wsgi.post_form'] = post_form
            self.__environ['wsgi.input'] = new_input
        else:
            post_form = (input, None, fs)
            self.__environ['wsgi.post_form'] = post_form
        return fs

    def get_response_sent_p(self):
        return self.__response_sent_p

    def get_low_level_headers(self):
        return self.__low_level_headers

    def get_buffer(self):
        return self.__buffer

    def write(self, string, flush=1):
        if isinstance(string, unicode):
            self.__buffer += string.encode('utf8')
        else:
            self.__buffer += string
        if flush:
            self.flush()

    def flush(self):
        self.send_http_header()
        if self.__buffer:
            self.__bytes_sent += len(self.__buffer)
            try:
                self.__write(self.__buffer)
            except IOError, err:
                if "failed to write data" in str(err) \
                       or "client connection closed" in str(err):
                    registerException()
                else:
                    raise
            self.__buffer = ''

    def set_content_type(self, content_type):
        self.__headers['content-type'] = content_type

    def get_content_type(self):
        return self.__headers['content-type']

    def send_http_header(self):
        if not self.__response_sent_p:
            if self.__allowed_methods and self.__status.startswith('405 ') or \
                   self.__status.startswith('501 '):
                self.__headers['Allow'] = ', '.join(self.__allowed_methods)
            ## See: <http://www.python.org/dev/peps/pep-0333/#the-write-callable>
            self.__write = self.__start_response(self.__status,
                                                 self.__low_level_headers)
            self.__response_sent_p = True

    def get_parsed_uri(self):
        # The parsed_uri tuple is as follows
        # (scheme, hostinfo, user, password, hostname, port, path, query, fragment)
        return (self.URLFields['URL_SCHEME'], \
                self.URLFields['HTTP_HOST'], None, None, \
                self.URLFields['SERVER_NAME'], self.URLFields['SERVER_PORT'], \
                self.URLFields['SCRIPT_NAME'] + self.URLFields['PATH_INFO'], \
                self.URLFields['QUERY_STRING'], None)

    def get_unparsed_uri(self):
        url = self.URLFields['SCRIPT_NAME'] + self.URLFields['PATH_INFO']
        if self.URLFields['QUERY_STRING']:
            url += '?' + self.URLFields['QUERY_STRING']
        return url

    def get_uri(self):
        return self.URLFields['SCRIPT_NAME'] + self.URLFields['PATH_INFO']

    def get_headers_in(self):
        return self.__headers_in

    def get_subprocess_env(self):
        return self.__environ

    def add_common_vars(self):
        pass

    def get_args(self):
        return self.URLFields['QUERY_STRING']

    def get_remote_ip(self):
        return self.__environ.get('REMOTE_ADDR')

    def get_remote_host(self, type=REMOTE_HOST):
        if type == REMOTE_NOLOOKUP:
            return self.__environ.get('REMOTE_ADDR')
        return self.__environ.get('')

    def get_header_only(self):
        return self.__environ['REQUEST_METHOD'] == 'HEAD'

    def set_status(self, status):
        self.__status = '%s %s' % (status,
                                   HTTP_STATUS_MAP.get(int(status),
                                                       'Explanation not available'))

    def get_status(self):
        return int(self.__status.split(' ')[0])

    def get_wsgi_status(self):
        return self.__status

    def sendfile(self, path, offset=0, the_len=-1):
        try:
            self.send_http_header()
            file_to_send = open(path)
            file_to_send.seek(offset)
            file_wrapper = FileWrapper(file_to_send)
            count = 0
            if the_len < 0:
                for chunk in file_wrapper:
                    count += len(chunk)
                    self.__bytes_sent += len(chunk)
                    self.__write(chunk)
            else:
                for chunk in file_wrapper:
                    if the_len >= len(chunk):
                        the_len -= len(chunk)
                        count += len(chunk)
                        self.__bytes_sent += len(chunk)
                        self.__write(chunk)
                    else:
                        count += the_len
                        self.__bytes_sent += the_len
                        self.__write(chunk[:the_len])
                        break
        except IOError, err:
            if "failed to write data" in str(err) or \
                   "client connection closed" in str(err):
                registerException()
            else:
                raise
        return self.__bytes_sent

    def set_content_length(self, content_length):
        if content_length is not None:
            self.__headers['content-length'] = str(content_length)
        else:
            del self.__headers['content-length']

    def is_https(self):
        return int(guess_scheme(self.__environ) == 'https')

    def get_method(self):
        return self.__environ['REQUEST_METHOD']

    def get_hostname(self):
        return self.URLFields['HTTP_HOST']

    def set_filename(self, filename):
        self.__filename = filename
        if self.__disposition_type is None:
            self.__disposition_type = 'inline'
        self.__headers['content-disposition'] = '%s; filename=%s' % \
                                                (self.__disposition_type,
                                                 self.__filename)

    def set_encoding(self, encoding):
        if encoding:
            self.__headers['content-encoding'] = str(encoding)
        else:
            del self.__headers['content-encoding']

    def get_bytes_sent(self):
        return self.__bytes_sent

    def log_error(self, message):
        self.__errors.write(message.strip() + '\n')

    def get_content_type_set_p(self):
        return bool(self.__headers['content-type'])

    def allow_methods(self, methods, reset=0):
        if reset:
            self.__allowed_methods = []
        self.__allowed_methods += [method.upper().strip() for method in methods]

    def get_allowed_methods(self):
        return self.__allowed_methods

    def readline(self, hint=None):
        ## the hint param is not part of wsgi pep, although
        ## it's great to exploit it in when reading FORM
        ## with large files, in order to avoid filling up the memory
        ## Too bad it's not there :-(
        return self.__environ['wsgi.input'].readline()

    def readlines(self, hint=-1):
        return self.__environ['wsgi.input'].readlines(hint)

    def read(self, size=-1):
        if size == -1:
            size = int(self.__environ['CONTENT_LENGTH'])
        return self.__environ['wsgi.input'].read(size)

    def register_cleanup(self, callback, data=None):
        self.__cleanups.append((callback, data))

    def get_cleanups(self):
        return self.__cleanups

    def get_prev(self):
        return self.__environ.get('HTTP_REFERER', '')

    def construct_url(self, supplied_uri):
        url = self.URLFields['URL_SCHEME']+'://'

        if self.URLFields['HTTP_HOST']:
            url += self.URLFields['HTTP_HOST']
        else:
            url += self.URLFields['SERVER_NAME']

            if self.URLFields['URL_SCHEME'] == 'https':
                if self.URLFields['SERVER_PORT'] != '443':
                    url += ':' + self.URLFields['SERVER_PORT']
            else:
                if self.URLFields['SERVER_PORT'] != '80':
                    url += ':' + self.URLFields['SERVER_PORT']

        url += self.URLFields['SERVER_NAME']
        url += supplied_uri

        return url

    content_type = property(get_content_type, set_content_type)
    parsed_uri = property(get_parsed_uri)
    unparsed_uri = property(get_unparsed_uri)
    uri = property(get_uri)
    headers_in = property(get_headers_in)
    subprocess_env = property(get_subprocess_env)
    args = property(get_args)
    header_only = property(get_header_only)
    status = property(get_status, set_status)
    method = property(get_method)
    hostname = property(get_hostname)
    filename = property(fset=set_filename)
    encoding = property(fset=set_encoding)
    bytes_sent = property(get_bytes_sent)
    content_type_set_p = property(get_content_type_set_p)
    allowed_methods = property(get_allowed_methods)
    response_sent_p = property(get_response_sent_p)
    form = property(get_post_form)
    remote_ip = property(get_remote_ip)
    remote_host = property(get_remote_host)
    prev = property(get_prev)

