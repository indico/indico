# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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
Some apache rewrites managed with mod_wsgi.
"""

import os
from MaKaC.common import Config

from indico.util.caching import cached_property
from indico.web.http_api import handlers as export_handlers


DIR_MODULES = os.path.dirname(export_handlers.__file__)


class ServerConfig(object):

    @cached_property
    def url_mappings(self):
        """
        url_mappings returns the modules and handlers for every page we want,
        in the form (hash, tuple)
        @hash: matching directory
        @tuple[0]: module, a pair in the form "(containingDir, file)"
        @tuple[1]: handler
        @tuple[2]: preprocessing function (if there's no function, '')
        @tuple[3]: parameters for the preprocessing function (dictionary)

        Add pages that need url parsing here.
        """
        return {'': ((self.htdocs_dir, 'index.py'), 'index', '', None), \
                    #'services':     ((DIR_SERVICES, 'handler.py'), 'handler', '', None), \
                    'event':        ((self.htdocs_dir, 'events.py'), 'index', 'genericRewrite', \
                                         {'queryReplacement': 'tag'}), \
                    'categ':        ((self.htdocs_dir, 'categoryDisplay.py'), 'index', 'genericRewrite', \
                                         {'queryReplacement': 'categId'}),
                #'export':       ((DIR_MODULES, 'wsgi_handler.py'), 'handler', '', None),
                #'api':          ((DIR_MODULES, 'wsgi_handler.py'), 'handler', '', None)
                }

    @cached_property
    def htdocs_dir(self):
        return Config.getInstance().getHtdocsDir()


SERVER_CONFIG = ServerConfig()


def is_static_path(path):
    """
    Returns True if path corresponds to an existing file under htdocs_dir.
    @param path: the path.
    @type path: string
    @return: True if path corresponds to an existing file under htdocs_dir.
    @rtype: bool
    """
    path = os.path.abspath(SERVER_CONFIG.htdocs_dir + path)
    if path.startswith(SERVER_CONFIG.htdocs_dir) and os.path.isfile(path):
        return path
    return None


def is_mp_legacy_publisher_path(req):
    """
    Finds the corresponding module and handler for the path given.
    Checks path corresponds to an existing Python file under htdocs_dir.
    @param path: the path.
    @type path: string
    @return: the path of the module to load and the function to call there.
    @rtype: tuple
    """
    path = req.URLFields['PATH_INFO'].split('/')
    startingDir = ''
    if len(path) > 1:
        startingDir = path[1]

    mappings = SERVER_CONFIG.url_mappings

    # First, we try to assign an existing redirection
    if startingDir in mappings:
        module, handler, function, params = mappings[startingDir]
        if callable(getattr(WSGIRedirection, function, None)):
            rwPage = WSGIRedirection(req, module, handler, startingDir)
            getattr(rwPage, function)(params)
        return (os.path.join(module[0], module[1]), handler)

    # Else, we try to find the called module
    for index, component in enumerate(path):
        if component.endswith('.py'):
            possible_module = os.path.abspath(SERVER_CONFIG.htdocs_dir + os.path.sep + \
                                              os.path.sep.join(path[:index + 1]))
            possible_handler = '/'.join(path[index + 1:]).strip()
            if not possible_handler:
                possible_handler = 'index'
            if os.path.exists(possible_module):
                return (possible_module, possible_handler)

    # If all fails, then we will load a static resource
    else:
        return None, None


class WSGIRedirection(object):
    """
    Redirections that need special treatment are handled by this class.
    """
    def __init__(self, req, module, handler, dir):
        self._dir = dir
        self._module = module
        self._handler = handler
        self._req = req
        # These two lines locate DIR in the PATH_INFO
        self._path = self._req.URLFields['PATH_INFO'].split('/')
        self._index = self._path.index(self._dir)

    def _pathRewrite(self, fileName):
        """
        Obtain the web base directory from the PATH_INFO,
        and then add the module to the path:
        '/indico/DIR/...' => '/indico' => '/indico/fileName'
        """
        newPathInfo = os.path.sep.join(self._path[:self._index]) + '/' + fileName
        self._req.URLFields['PATH_INFO'] = newPathInfo

    def _queryRewrite(self, query):
        """
        Rewrites the QUERY_STRING, putting everything after DIR in it
        Example of URL:
        http://indico.cern.ch/DIR/index.py?my=messy/short.py?tag=true
         =>
        http://indico.cern.ch/fileName?query=index.py?my=messy/short.py?tag=true
        """
        newQueryString = query + '='

        # remove trailing slashes
        filteredPath = self._path[self._index + 1:]
        if filteredPath[-1] == '':
            filteredPath = filteredPath[:-1]

        newQueryString += '/'.join(filteredPath)

        if self._req.URLFields['QUERY_STRING']:
            newQueryString += '?' + self._req.URLFields['QUERY_STRING']
        self._req.URLFields['QUERY_STRING'] = newQueryString

    # Add the preprocessing functions for rewriting here.
    def genericRewrite(self, params):
        """
        Rewrites a /DIR/ directory tag with queryReplacement
        Example:
        http://indico.cern.ch/DIR/108?my=messy/short.py?tag=true
         =>
        http://indico.cern.ch/MODULE[1]?queryReplacement=108?my=messy/short.py?tag=true
        """
        self._pathRewrite(self._module[1])
        self._queryRewrite(params['queryReplacement'])

