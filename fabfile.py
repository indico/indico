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
from fabric.colors import red, green, yellow, cyan
from fabvenv import virtualenv


NODE_VERSION = '0.10.9'
SUBMODULES = ['compass', 'jquery', 'qtip2']
ASSET_TYPES = ['js', 'sass', 'css']
DEFAULT_VERSIONS = ['2.6', '2.7']
DEFAULT_BUILD_DIR = '/tmp/indico-build'


# Generated vars

DEFAULT_INDICO_DIR = os.path.dirname(__file__)
DEFAULT_EXT_DIR = os.path.join(DEFAULT_INDICO_DIR, 'ext_modules')
DEFAULT_NODE_ENV = os.path.join(DEFAULT_EXT_DIR, 'node_env')
DEFAULT_TARGET_DIR = os.path.join(DEFAULT_INDICO_DIR, 'indico/htdocs')

RECIPES = {}


def recipe(name):
    def _wrapper(f):
        RECIPES[name] = f
        task(f)
    return _wrapper


# Decorators

def node_env(path=DEFAULT_NODE_ENV):
    return prefix('source {0}'.format(os.path.join(path, 'bin/activate')))


def pythonbrew(version, env):
    script = local('pythonbrew venv print_activate {0} -p {1}'.format(env, version), capture=True)
    return prefix('source {0}'.format(script))


# Util functions

def create_node_env(version=NODE_VERSION, path=DEFAULT_NODE_ENV):
    with settings(warn_only=True):
        local('nodeenv -c -n {0} {1}'.format(version, path))


def lib_dir(src_dir, dtype):
    target_dir = os.path.join(src_dir, 'indico', 'htdocs')
    return os.path.join(target_dir, dtype, 'lib')


def _install_dependencies(mod_name, sub_path, dtype, src_dir, ext_dir):
    dest_dir = os.path.join(lib_dir(src_dir, dtype), mod_name)
    local('mkdir -p {0}'.format(dest_dir))
    local('cp -R {0} {1}/'.format(
        os.path.join(ext_dir, mod_name, sub_path),
        dest_dir))


# Recipes

@recipe('compass')
def install_compass(src_dir, ext_dir, n_env):
    """
    Install compass stylesheets from Git
    """
    _install_dependencies('compass', 'frameworks/compass/stylesheets', 'sass', src_dir, ext_dir)


@recipe('jquery')
def install_jquery(src_dir, ext_dir, n_env):
    """
    Install jquery from Git
    """
    with node_env(n_env):
        with lcd(os.path.join(ext_dir, 'jquery')):
            local('npm install')
            local('grunt')
            dest_dir = lib_dir(src_dir, 'js')
            local('mkdir -p {0}'.format(dest_dir))
            local('cp dist/jquery.js {0}/'.format(dest_dir))


@recipe('qtip2')
def install_qtip2(src_dir, ext_dir, n_env):
    """
    Install qtip2 from Git
    """
    with node_env(n_env):
        with lcd(os.path.join(ext_dir, 'qtip2')):
            local('git submodule update')
            local('npm install')
            local('grunt --plugins="tips modal viewport svg" init clean concat:dist concat:css concat:libs replace')
            dest_dir_js, dest_dir_css = lib_dir(src_dir, 'js'), lib_dir(src_dir, 'css')
            local('mkdir -p {0} {1}'.format(dest_dir_js, dest_dir_css))
            local('cp dist/jquery.qtip.js {0}/'.format(dest_dir_js))
            local('cp dist/jquery.qtip.css {0}/'.format(dest_dir_css))


# Tasks

@task
def install(recipe_name, **dir_info):
    """
    Install a module given the recipe name
    """
    RECIPES[recipe_name](**dir_info)


@task
def init_submodules(src_dir='.'):
    """
    Initialize submodules (fetch them from external Git repos)
    """

    print green("Initializing submodules")
    with lcd(src_dir):
        local('git submodule init')
        local('git submodule update')


def _install_deps(**dir_info):
    """
    Install asset dependencies
    """
    print green("Installing asset dependencies...")
    for recipe_name in RECIPES:
        print cyan("Installing {0}".format(recipe_name))
        install(recipe_name, **dir_info)


@task
def setup_deps(n_env=DEFAULT_NODE_ENV, n_version=NODE_VERSION, src_dir=DEFAULT_INDICO_DIR):
    """
    Setup (fetch and install) dependencies for Indico assets
    """

    # initialize submodules if they haven't yet been
    init_submodules(src_dir)

    dir_info = dict(
        src_dir=src_dir,
        ext_dir=os.path.join(src_dir, 'ext_modules'),
        n_env=os.path.join(src_dir, 'ext_modules', 'node_env'))

    if not os.path.exists(n_env):
        create_node_env(path=n_env, version=n_version)

    with node_env(n_env):
        local('npm install -g grunt-cli')

    _install_deps(**dir_info)


@task
def clean_deps(src_dir=DEFAULT_INDICO_DIR):
    """
    Clean up generated files
    """
    for dtype in ASSET_TYPES:
        local('rm -rf {0}/*'.format(lib_dir(src_dir, dtype)))


@task
def tarball(build_dir=DEFAULT_BUILD_DIR):
    setup_deps(n_env=os.path.join(build_dir, 'indico', 'ext_modules', 'node_env'),
               src_dir=os.path.join(build_dir, 'indico'))
    local('python setup.py sdist')


@task
def package_release(versions=DEFAULT_VERSIONS, build_dir=DEFAULT_BUILD_DIR):
    # get current branch
    current_branch = local('git rev-parse --abbrev-ref HEAD', capture=True)

    with prefix('source ~/.pythonbrew/etc/bashrc'):
        local('mkdir -p {0}'.format(build_dir))
        with lcd(build_dir):
            # clone this same repo
            if os.path.exists('indico'):
                print yellow("Repository seems to already exist.")
                with lcd('indico'):
                    local('git fetch')
            else:
                local('git clone {0} indico'.format(os.path.dirname(__file__)))
            with lcd('indico'):
                print green("Checking out branch '{0}'".format(current_branch))
                local('git checkout origin/{0}'.format(current_branch))

                # Build source tarball
                tarball(build_dir=build_dir)

                # Build binaries (EGG)
                for version in versions:
                    with pythonbrew(version, 'indico'):
                        local('pip install -r requirements.txt')
                        local('python setup.py bdist_egg')
                        print green(local('ls -lah dist/', capture=True))
