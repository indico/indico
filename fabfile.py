# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN)
##
## Indico is free software: you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico.  If not, see <http://www.gnu.org/licenses/>.

"""
fabfile for Indico development operations
"""

import os
from fabric.api import local, lcd, task
from fabric.context_managers import prefix, settings


NODE_VERSION = '0.10.9'
SUBMODULES = ['compass', 'jquery', 'qtip2']
ASSET_TYPES = ['js', 'sass', 'css']


# Generated vars - do not change!
EXT_DIR = os.path.join(os.path.dirname(__file__), 'ext_modules')
NODE_ENV = os.path.join(EXT_DIR, 'node_env')
TARGET_DIR = os.path.join(os.path.dirname(__file__), 'indico/htdocs')


def lib_dir(dtype):
    return os.path.join(TARGET_DIR, dtype, 'lib')


def node_env(path=NODE_ENV):
    return prefix('source {0}'.format(os.path.join(path, 'bin/activate')))


def create_node_env(version=NODE_VERSION, path=NODE_ENV):
    with settings(warn_only=True):
        local('nodeenv -c -n {0} {1}'.format(version, path))


def _init_submodule(name):
    path = os.path.join(EXT_DIR, name)
    local('git submodule init {0}'.format(path))
    local('git submodule update {0}'.format(path))


def _install_dependencies(mod_name, sub_path, dtype):
    dest_dir = os.path.join(lib_dir(dtype), mod_name)
    local('mkdir -p {0}'.format(dest_dir))
    local('cp -R {0} {1}/'.format(
        os.path.join(EXT_DIR, mod_name, sub_path),
        dest_dir))


@task
def install_compass():
    """
    Install compass stylesheets from Git
    """
    _install_dependencies('compass', 'frameworks/compass/stylesheets', 'scss')


@task
def install_jquery():
    """
    Install jquery from Git
    """
    with node_env(NODE_ENV):
        with lcd(os.path.join(EXT_DIR, 'jquery')):
            local('npm install')
            local('grunt')
            dest_dir = lib_dir('js')
            local('mkdir -p {0}'.format(dest_dir))
            local('cp dist/jquery.js {0}/'.format(dest_dir))


@task
def install_qtip2():
    """
    Install qtip2 from Git
    """
    with node_env(NODE_ENV):
        with lcd(os.path.join(EXT_DIR, 'qtip2')):
            local('git submodule update')
            local('npm install')
            local('grunt --plugins="tips modal viewport svg" init clean concat:dist concat:css concat:libs replace')
            dest_dir_js, dest_dir_css = lib_dir('js'), lib_dir('css')
            local('mkdir -p {0} {1}'.format(dest_dir_js, dest_dir_css))
            local('cp dist/jquery.qtip.js {0}/'.format(dest_dir_js))
            local('cp dist/jquery.qtip.css {0}/'.format(dest_dir_css))


@task
def init_submodules():
    """
    Initialize submodules (fetch them from external Git repos)
    """
    local('git submodule update')


def _install_deps():
    """
    Install asset dependencies
    """
    install_compass()
    install_jquery()
    install_qtip2()


@task
def setup_deps():
    """
    Setup (fetch and install) dependencies for Indico assets
    """

    # initialize submodules if they haven't yet been
    init_submodules()

    if not os.path.exists(NODE_ENV):
        create_node_env()

    with node_env(NODE_ENV):
        local('npm install -g grunt-cli')

    _install_deps()


@task
def clean_deps():
    """
    Clean up generated files
    """
    for dtype in ASSET_TYPES:
        local('rm -rf {0}/*'.format(lib_dir(dtype)))