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
import sys
import glob
from contextlib import contextmanager

from fabric.api import local, lcd, task, env
from fabric.context_managers import prefix, settings
from fabric.colors import red, green, yellow, cyan
from fabric.contrib import console


ASSET_TYPES = ['js', 'sass', 'css']
PYTHONBREW_PATH = os.path.expanduser('~/.pythonbrew')
DOC_DIRS = ['guides']

DEFAULT_NODE_VERSION = '0.10.10'
DEFAULT_VERSIONS = ['2.6', '2.7']

# Generated vars

DEFAULT_INDICO_DIR = os.path.dirname(__file__)
DEFAULT_BUILD_DIR = os.path.join(DEFAULT_INDICO_DIR, 'dist', 'indico-build')

RECIPES = {}

env.update({
    'global_node': False,
    'node_version': DEFAULT_NODE_VERSION,
    'node_env_path': os.path.join(DEFAULT_INDICO_DIR, 'ext_modules', 'node_env'),
    'versions': DEFAULT_VERSIONS,

    'build_dir': DEFAULT_BUILD_DIR,
    'src_dir': DEFAULT_INDICO_DIR,
    'ext_dir': os.path.join(DEFAULT_INDICO_DIR, 'ext_modules'),
    'target_dir': os.path.join(DEFAULT_INDICO_DIR, 'indico/htdocs'),
    'system_node': False
})


def recipe(name):
    def _wrapper(f):
        RECIPES[name] = f
    return _wrapper


# Decorators

@contextmanager
def node_env():
    if env.system_node:
        yield
    else:
        with prefix('. {0}'.format(os.path.join(env.node_env_path, 'bin/activate'))):
            yield


def pythonbrew():
    return prefix('. {0}'.format(os.path.join(PYTHONBREW_PATH, 'etc', 'bashrc')))


@contextmanager
def pythonbrew_env(version, env):
    with pythonbrew():
        with prefix('pythonbrew venv use {0} -p {1}'.format(env, version)):
            yield


def pythonbrew_cmd(cmd, **kwargs):
    with pythonbrew():
        return local('pythonbrew {0}'.format(cmd), **kwargs)


# Util functions

def create_node_env():
    with settings(warn_only=True):
        local('nodeenv -c -n {0} {1}'.format(env.node_version, env.node_env_path))


def lib_dir(src_dir, dtype):
    target_dir = os.path.join(src_dir, 'indico', 'htdocs')
    return os.path.join(target_dir, dtype, 'lib')


def _check_pythonbrew(versions):
    """
    Check that pythonbrew is installed and set up the compilers/virtual envs
    in case they do not exist
    """

    try:
        import pythonbrew
        HAS_PYTHONBREW = True
    except ImportError:
        HAS_PYTHONBREW = False

    if not HAS_PYTHONBREW:
        print red("Can't find pythonbrew!")
        print yellow("Are you sure you have installed it? (pip install pythonbrew)")
        sys.exit(-2)

    elif not os.path.exists(PYTHONBREW_PATH):
        print yellow("Running pythonbrew_install")
        local('pythonbrew_install')

    # list available pythonbrew versions
    av_versions = list(entry.strip() for entry in
                       pythonbrew_cmd('list', capture=True).split('\n')[1:])

    for version in versions:
        if ('Python-' + version) not in av_versions:
            print green('Installing Python {0}'.format(version))
            pythonbrew_cmd('install {0}'.format(version), capture=True)

        # check envs that are available
        envs = list(entry.strip() for entry in
                    pythonbrew_cmd('venv -p {0} list'.format(version), capture=True).split('\n')[1:])

        if 'indico' not in envs:
            pythonbrew_cmd('venv -p {0} create indico'.format(version))


def _check_present(executable, message="Please install it first."):
    """
    Check that executable exists in $PATH
    """
    with settings(warn_only=True):
        if local('which {0} > /dev/null && echo $?'.format(executable), capture=True) != '0':
            print red('{0} is not available in this system. {1}'.format(executable, message))
            sys.exit(-2)


def _safe_rm(path, recursive=False, ask=True):
    with lcd('/tmp'):
        if path[0] != '/':
            path = os.path.join(env.lcwd, path)
        if ask:
            files = glob.glob(path)
            if files:
                print yellow("The following files are going to be deleted:\n  ") + '\n  '.join(files)
                if console.confirm(cyan("Are you sure you want to delete them?")):
                    local('rm {0}{1}'.format('-rf ' if recursive else '', path))
                else:
                    print red("Delete operation cancelled")
        else:
            local('rm {0}{1}'.format('-rf ' if recursive else '', path))


def _install_dependencies(mod_name, sub_path, dtype, dest_subpath=None):
    l_dir = lib_dir(env.src_dir, dtype)
    dest_dir = os.path.join(l_dir, dest_subpath) if dest_subpath else l_dir
    local('mkdir -p {0}'.format(dest_dir))
    local('cp -R {0} {1}/'.format(
        os.path.join(env.ext_dir, mod_name, sub_path),
        dest_dir))


# Recipes

@recipe('compass')
def install_compass():
    """
    Install compass stylesheets from Git
    """
    _install_dependencies('compass', 'frameworks/compass/stylesheets/*', 'sass', 'compass')


@recipe('jquery')
def install_jquery():
    """
    Install jquery from Git
    """
    with node_env():
        with lcd(os.path.join(env.ext_dir, 'jquery')):
            local('npm install')
            local('grunt')
            dest_dir = lib_dir(env.src_dir, 'js')
            local('mkdir -p {0}'.format(dest_dir))
            local('cp dist/jquery.js {0}/'.format(dest_dir))


@recipe('underscore')
def install_underscore():
    """
    Install jquery from Git
    """
    _install_dependencies('underscore', 'underscore.js', 'js')


@recipe('qtip2')
def install_qtip2():
    """
    Install qtip2 from Git
    """
    with node_env():
        with lcd(os.path.join(env.ext_dir, 'qtip2')):
            local('git submodule init')
            local('git submodule update')
            local('npm install')
            local('grunt --plugins="tips modal viewport svg" init clean concat:dist concat:css concat:libs replace')
            dest_dir_js, dest_dir_css = lib_dir(env.src_dir, 'js'), lib_dir(env.src_dir, 'css')
            local('mkdir -p {0} {1}'.format(dest_dir_js, dest_dir_css))
            local('cp dist/jquery.qtip.js {0}/'.format(dest_dir_js))
            local('cp dist/jquery.qtip.css {0}/'.format(dest_dir_css))


@recipe('jquery-ui-multiselect')
def install_jquery_ui_multiselect():
    """
    Install jquery ui multiselect widget from Git
    """
    with node_env():
        with lcd(os.path.join(env.ext_dir, 'jquery-ui-multiselect')):
            dest_dir_js = lib_dir(env.src_dir, 'js')
            dest_dir_css = lib_dir(env.src_dir, 'css')
            local('mkdir -p {0} {1}'.format(dest_dir_js, dest_dir_css))
            local('cp src/jquery.multiselect.js {0}/'.format(dest_dir_js))
            local('cp src/jquery.multiselect.filter.js {0}/'.format(dest_dir_js))
            local('cp jquery.multiselect.css {0}/'.format(dest_dir_css))
            local('cp jquery.multiselect.filter.css {0}/'.format(dest_dir_css))


# Tasks

@task
def install(recipe_name):
    """
    Install a module given the recipe name
    """
    RECIPES[recipe_name]()


@task
def init_submodules(src_dir='.'):
    """
    Initialize submodules (fetch them from external Git repos)
    """

    print green("Initializing submodules")
    with lcd(src_dir):
        local('git submodule init')
        local('git submodule update')


def _install_deps():
    """
    Install asset dependencies
    """
    print green("Installing asset dependencies...")
    for recipe_name in RECIPES:
        print cyan("Installing {0}".format(recipe_name))
        install(recipe_name)


@task
def setup_deps(n_env=None, n_version=None, src_dir=None, system_node=None):
    """
    Setup (fetch and install) dependencies for Indico assets
    """

    src_dir = src_dir or env.src_dir
    n_env = n_env or env.node_env_path
    system_node = system_node if system_node is not None else env.system_node

    # initialize submodules if they haven't yet been
    init_submodules(src_dir)

    ext_dir = os.path.join(src_dir, 'ext_modules')

    _check_present('curl')

    with settings(node_env_path=n_env or os.path.join(ext_dir, 'node_env'),
                  node_version=n_version or env.node_version,
                  system_node=system_node,
                  src_dir=src_dir,
                  ext_dir=ext_dir):

        if not system_node and not os.path.exists(n_env):
            create_node_env()

        with node_env():
            local('npm install -g grunt-cli')

        _install_deps()


@task
def clean_deps(src_dir=None):
    """
    Clean up generated files
    """

    for dtype in ASSET_TYPES:
        _safe_rm('{0}/*'.format(lib_dir(src_dir or env.src_dir, dtype)), recursive=True)


@task
def cleanup(build_dir=None, force=False):
    """
    Clean up build environment
    """
    _safe_rm('{0}'.format(build_dir or env.build_dir), recursive=True, ask=(not force))


@task
def tarball(src_dir=None):
    """
    Create a binary indico distribution
    """

    src_dir = src_dir or env.src_dir

    make_docs(src_dir)

    setup_deps(n_env=os.path.join(src_dir, 'ext_modules', 'node_env'),
               src_dir=src_dir)
    local('python setup.py -q sdist')


@task
def make_docs(src_dir=None, build_dir=None):
    """
    Generate Indico docs
    """
    _check_present('pdflatex')

    src_dir = src_dir or env.src_dir

    if build_dir is None:
        target_dir = os.path.join(src_dir, 'indico', 'htdocs', 'ihelp')
    else:
        target_dir = os.path.join(build_dir or env.build_dir, 'indico', 'htdocs', 'ihelp')

    print green('Generating documentation')
    with lcd(os.path.join(src_dir, 'doc')):
        for d in DOC_DIRS:
            with lcd(d):
                local('make html')
                local('make latex')
                local('rm -rf {0}/*'.format(os.path.join(target_dir, 'html')))
                local('mv build/html/* {0}'.format(os.path.join(target_dir, 'html')))

        with lcd(os.path.join('guides', 'build', 'latex')):
            local('make all-pdf')
            local('mv *.pdf {0}'.format(os.path.join(target_dir, 'pdf')))

        print green('Cleaning up')
        for d in DOC_DIRS:
            with lcd(d):
                local('make clean')


@task
def package_release(versions=None, build_dir=None, system_node=False):
    """
    Create an Indico release - source and binary distributions
    """

    versions = versions or env.versions
    build_dir = build_dir or env.build_dir

    # get current branch
    current_branch = local('git rev-parse --abbrev-ref HEAD', capture=True)

    local('mkdir -p {0}'.format(build_dir))

    _check_pythonbrew(versions)

    with lcd(build_dir):
        # clone this same repo
        if os.path.exists(os.path.join(build_dir, 'indico')):
            print yellow("Repository seems to already exist.")
            with lcd('indico'):
                local('git fetch')
        else:
            local('git clone {0} indico'.format(os.path.dirname(__file__)))
        with lcd('indico'):
            print green("Checking out branch '{0}'".format(current_branch))
            local('git checkout origin/{0}'.format(current_branch))

            with settings(system_node=system_node):
                # Build source tarball
                tarball(os.path.join(build_dir, 'indico'))

            # Build binaries (EGG)
            for version in versions:
                with pythonbrew_env(version, 'indico'):
                    local('pip -q install -r requirements.txt')
                    local('python setup.py -q bdist_egg')
                    pass
            print green(local('ls -lah dist/', capture=True))

    cleanup(build_dir, force=True)
