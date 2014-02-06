# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN)
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
import re
import sys
import glob
import shutil
import json
import getpass
from contextlib import contextmanager
from urlparse import urljoin

from fabric.api import local, lcd, task, env
from fabric.context_managers import prefix, settings
from fabric.colors import red, green, yellow, cyan
from fabric.contrib import console


ASSET_TYPES = ['js', 'sass', 'css']
DOC_DIRS = ['guides']
RECIPES = {}

env.conf = 'fabfile.conf'
env.src_dir = os.path.dirname(__file__)
execfile(env.conf, {}, env)
env.ext_dir = os.path.join(env.src_dir, env.ext_dirname)
env.target_dir = os.path.join(env.src_dir, env.target_dirname)
env.node_env_path = os.path.join(env.src_dir, env.node_env_dirname)


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


@contextmanager
def pyenv_env(version):
    cmd_dir = os.path.join(env.pyenv_dir, 'versions', 'indico-build-{0}'.format(version), 'bin')
    with prefix('PATH={0}:$PATH'.format(cmd_dir)):
        yield


def pyenv_cmd(cmd, **kwargs):
    cmd_dir = os.path.join(env.pyenv_dir, 'bin')
    return local('{0}/pyenv {1}'.format(cmd_dir, cmd), **kwargs)


# Util functions

def create_node_env():
    with settings(warn_only=True):
        local('nodeenv -c -n {0} {1}'.format(env.node_version, env.node_env_path))


def lib_dir(src_dir, dtype):
    target_dir = os.path.join(src_dir, 'indico', 'htdocs')
    return os.path.join(target_dir, dtype, 'lib')


def _check_pyenv(py_versions):
    """
    Check that pyenv is installed and set up the compilers/virtual envs
    in case they do not exist
    """

    if not os.path.isdir(env.pyenv_dir):
        print red("Can't find pyenv!")
        print yellow("Are you sure you have installed it?")
        sys.exit(-2)

    # list available pyenv versions
    av_versions = list(entry.strip() for entry in pyenv_cmd('versions', capture=True).split('\n')[1:])

    for py_version in py_versions:
        if (py_version) not in av_versions:
            print green('Installing Python {0}'.format(py_version))
            pyenv_cmd('install {0}'.format(py_version), capture=True)

        pyenv_cmd("virtualenv -f {0} indico-build-{0}".format(py_version))


def _check_present(executable, message="Please install it first."):
    """
    Check that executable exists in $PATH
    """

    with settings(warn_only=True):
        if local('which {0} > /dev/null && echo $?'.format(executable), capture=True) != '0':
            print red('{0} is not available in this system. {1}'.format(executable, message))
            sys.exit(-2)


def _safe_rm(path, recursive=False, ask=True):
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


def _cp_tree(dfrom, dto, exclude=[]):
    """
    Simple copy with exclude option
    """
    if dfrom[0] != '/':
        dfrom = os.path.join(env.lcwd, dfrom)
    if dto[0] != '/':
        dto = os.path.join(env.lcwd, dto)

    print "{0} -> {1}".format(dfrom, dto)

    shutil.copytree(dfrom, dto, ignore=shutil.ignore_patterns(*exclude))


def _install_dependencies(mod_name, sub_path, dtype, dest_subpath=None):
    l_dir = lib_dir(env.src_dir, dtype)
    dest_dir = os.path.join(l_dir, dest_subpath) if dest_subpath else l_dir
    local('mkdir -p {0}'.format(dest_dir))
    local('cp -R {0} {1}/'.format(
        os.path.join(env.ext_dir, mod_name, sub_path),
        dest_dir))


# Recipes

@recipe('angular')
def install_angular():
    """
    Install Angular.js from Git
    """
    with node_env():
        with lcd(os.path.join(env.ext_dir, 'angular')):
            local('npm install')
            local('grunt clean buildall copy write compress')
            dest_dir_js = lib_dir(env.src_dir, 'js')
            dest_dir_css = lib_dir(env.src_dir, 'css')
            local('mkdir -p {0}'.format(dest_dir_js))
            local('cp build/angular.js {0}/'.format(dest_dir_js))
            local('cp build/angular-resource.js {0}/'.format(dest_dir_js))
            local('cp build/angular-sanitize.js {0}/'.format(dest_dir_js))
            local('cp css/angular.css {0}'.format(dest_dir_css))


@recipe('ui-sortable')
def install_ui_sortable():
    """
    Install angular ui-sortable from Git
    """
    with node_env():
        with lcd(os.path.join(env.ext_dir, 'ui-sortable')):
            dest_dir_js = lib_dir(env.src_dir, 'js')
            local('mkdir -p {0}'.format(dest_dir_js))
            local('cp src/sortable.js {0}/'.format(dest_dir_js))


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


@recipe('MathJax')
def install_mathjax():
    """
    Install MathJax from Git
    """

    dest_dir = os.path.join(lib_dir(env.src_dir, 'js'), 'mathjax/')
    mathjax_js = os.path.join(dest_dir, 'MathJax.js')

    with lcd(os.path.join(env.ext_dir, 'mathjax')):
        local('rm -rf {0}'.format(os.path.join(dest_dir)))
        _cp_tree('unpacked/', dest_dir, exclude=["AM*", "MML*", "Accessible*", "Safe*"])
        _cp_tree('images/', os.path.join(dest_dir, 'images'))
        _cp_tree('fonts/', os.path.join(dest_dir, 'fonts'), exclude=["png"])

    with open(mathjax_js, 'r') as f:
        data = f.read()
        # Uncomment 'isPacked = true' line
        data = re.sub(r'//\s*(MathJax\.isPacked\s*=\s*true\s*;)', r'\1', data, re.MULTILINE)

    with open(mathjax_js, 'w') as f:
        f.write(data)


@recipe('PageDown')
def install_pagedown():
    """
    Install PageDown from Git (mirror!)
    """
    with lcd(os.path.join(env.ext_dir, 'pagedown')):
        dest_dir = os.path.join(lib_dir(env.src_dir, 'js'), 'pagedown/')
        local('mkdir -p {0}'.format(dest_dir))
        local('cp *.js {0}'.format(dest_dir))


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
        local('pwd')
        local('git submodule update --init --recursive')


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

                print d

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
def package_release(py_versions=None, system_node=False, indico_versions=None, upstream=None, no_clean=False, force_clean=False):
    """
    Create an Indico release - source and binary distributions
    """

    DEVELOP_REQUIRES = ['pojson>=0.4', 'termcolor', 'werkzeug', 'nodeenv', 'fabric', 'sphinx', 'repoze.sphinx.autointerface']

    py_versions = py_versions.split('/') if py_versions else env.py_versions
    _check_pyenv(py_versions)

    if not no_clean:
        if not force_clean and not console.confirm(red("This will reset your repository to its initial "
            "state (you will lose all files that are not under Git version control). Do you want to continue?"),
            default=False):
            sys.exit(2)

        local('git clean -dx')

    with pyenv_env(py_versions[-1]):
        local('pip -q install {0}'.format(' '.join(DEVELOP_REQUIRES + ['babel'])))

        print green('Generating '), cyan('tarball')

        with settings(system_node=system_node):
            # Build source tarball
            tarball(os.path.dirname(__file__))

    # Build binaries (EGG)
    for py_version in py_versions:
        with pyenv_env(py_version):
            print green('Generating '), cyan('egg for Python {0}'.format(py_version))
            local('pip -q install {0}'.format(' '.join(DEVELOP_REQUIRES + ['babel'])))
            local('python setup.py -q bdist_egg')

    print green(local('ls -lah dist/', capture=True))
