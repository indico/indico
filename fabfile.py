# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

"""
fabfile for Indico development operations
"""

import glob
import json
import os
import re
import shutil
import sys
from contextlib import contextmanager

from fabric.api import env, lcd, local, task
from fabric.colors import cyan, green, red, yellow
from fabric.context_managers import prefix, settings
from fabric.contrib import console


ASSET_TYPES = ['js', 'sass', 'css']
RECIPES = {}
SOURCE_DIR = os.path.dirname(__file__)

CKBUILDER_CONFIG = {
    'skin': 'moono-lisa',
    'languages': {'en': 1, 'es': 1, 'fr': 1},
    'plugins': {
        'a11yhelp': 1, 'basicstyles': 1, 'blockquote': 1, 'clipboard': 1, 'colorbutton': 1, 'colordialog': 1,
        'contextmenu': 1, 'elementspath': 1, 'enterkey': 1, 'entities': 1, 'find': 1, 'floatingspace': 1, 'font': 1,
        'format': 1, 'horizontalrule': 1, 'htmlwriter': 1, 'image': 1, 'indentlist': 1, 'justify': 1, 'link': 1,
        'list': 1, 'magicline': 1, 'maximize': 1, 'pastefromword': 1, 'pastetext': 1, 'removeformat': 1, 'resize': 1,
        'showborders': 1, 'sourcearea': 1, 'specialchar': 1, 'stylescombo': 1, 'tab': 1, 'table': 1, 'tabletools': 1,
        'toolbar': 1, 'undo': 1, 'wysiwygarea': 1
    },
    'ignore': [
        '.DS_Store', '.bender', '.editorconfig', '.gitattributes', '.gitignore', '.idea', '.jscsrc', '.jshintignore',
        '.jshintrc', '.mailmap', 'README.md', 'bender-err.log', 'bender-out.log', 'bender.js', 'dev', 'gruntfile.js',
        'less', 'node_modules', 'package.json', 'tests'
    ],
}

env.update({
    'src_dir': SOURCE_DIR,
    'ext_dir': os.path.join(SOURCE_DIR, 'ext_modules'),
    'target_dir': os.path.join(SOURCE_DIR, 'indico', 'htdocs'),
    'node_env_path': os.path.join(SOURCE_DIR, 'ext_modules', 'node_env'),
    'node_version': '4.2.2',
    'system_node': False,
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


def grunt(args):
    cmd = os.path.join(env.src_dir, 'node_modules/.bin/grunt')
    local('{} {}'.format(cmd, args))


# Util functions
def create_node_env():
    with settings(warn_only=True):
        local('nodeenv -c -n {0} {1}'.format(env.node_version, env.node_env_path))


def lib_dir(src_dir, dtype):
    target_dir = os.path.join(src_dir, 'indico', 'htdocs')
    return os.path.join(target_dir, dtype, 'lib')


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
    with node_env():
        with lcd(os.path.join(env.ext_dir, 'angular')):
            local('npm install')
            grunt('clean buildall copy write compress')
            dest_dir_js = lib_dir(env.src_dir, 'js')
            dest_dir_css = lib_dir(env.src_dir, 'css')
            local('mkdir -p {0}'.format(dest_dir_js))
            local('cp build/angular.js {0}/'.format(dest_dir_js))
            local('cp build/angular-resource.js {0}/'.format(dest_dir_js))
            local('cp build/angular-sanitize.js {0}/'.format(dest_dir_js))
            local('cp css/angular.css {0}'.format(dest_dir_css))


@recipe('chartist.js')
def install_chartist_js():
    with node_env():
        with lcd(os.path.join(env.ext_dir, 'chartist.js')):
            dest_dir_js = os.path.join(lib_dir(env.src_dir, 'js'), 'chartist.js/')
            dest_dir_css = os.path.join(lib_dir(env.src_dir, 'css'), 'chartist.js/')
            local('mkdir -p {0}'.format(dest_dir_js))
            local('mkdir -p {0}'.format(dest_dir_css))
            local('cp dist/chartist.js {0}/'.format(dest_dir_js))
            local('cp dist/scss/chartist.scss {0}/'.format(dest_dir_css))
            local('cp -r dist/scss/settings {0}/'.format(dest_dir_css))


@recipe('ui-sortable')
def install_ui_sortable():
    with node_env():
        with lcd(os.path.join(env.ext_dir, 'ui-sortable')):
            dest_dir_js = lib_dir(env.src_dir, 'js')
            local('mkdir -p {0}'.format(dest_dir_js))
            local('cp src/sortable.js {0}/'.format(dest_dir_js))


@recipe('compass')
def install_compass():
    _install_dependencies('compass', 'frameworks/compass/stylesheets/*', 'sass', 'compass')


@recipe('jquery')
def install_jquery():
    with node_env():
        with lcd(os.path.join(env.ext_dir, 'jquery')):
            local('npm install')
            grunt('uglify dist')
            dest_dir = lib_dir(env.src_dir, 'js')
            local('mkdir -p {0}'.format(dest_dir))
            local('cp dist/jquery.js {0}/'.format(dest_dir))


@recipe('jed')
def install_jed():
    with lcd(os.path.join(env.ext_dir, 'Jed')):
        dest_dir = lib_dir(env.src_dir, 'js')
        local('mkdir -p {0}'.format(dest_dir))
        local('cp jed.js {0}/'.format(dest_dir))


@recipe('jqplot')
def install_jqplot():
    """Install jQPlot from Git"""
    plugins = ['axis', 'bar', 'cursor', 'highlighter', 'points', 'text']
    with lcd(os.path.join(env.ext_dir, 'jqplot')):
        dest_dir_js = os.path.join(lib_dir(env.src_dir, 'js'), 'jqplot')
        dest_dir_css = lib_dir(env.src_dir, 'css')
        dest_dir_js_core = os.path.join(dest_dir_js, 'core')
        dest_dir_js_plugins = os.path.join(dest_dir_js, 'plugins')
        local('mkdir -p {0} {1}'.format(dest_dir_js_core, dest_dir_css))
        local('cp src/core/*.js {0}'.format(dest_dir_js_core))
        local('cp src/core/*.css {0}'.format(dest_dir_css))
        for plugin_name in plugins:
            dest = os.path.join(dest_dir_js_plugins, plugin_name)
            local('mkdir -p {0}'.format(dest))
            local('cp src/plugins/{0}/* {1}'.format(plugin_name, dest))


@recipe('underscore')
def install_underscore():
    """
    Install underscore from Git
    """
    _install_dependencies('underscore', 'underscore.js', 'js')


@recipe('rrule')  # rrule.js
def install_rrule():
    """
    Install rrule from Git
    """
    _install_dependencies('rrule', 'lib/rrule.js', 'js')


@recipe('qtip2')
def install_qtip2():
    with node_env():
        with lcd(os.path.join(env.ext_dir, 'qtip2')):
            local('npm install')
            grunt('--plugins="tips modal viewport svg" init clean concat:dist concat:css concat:libs replace')
            dest_dir_js, dest_dir_css = lib_dir(env.src_dir, 'js'), lib_dir(env.src_dir, 'css')
            local('mkdir -p {0} {1}'.format(dest_dir_js, dest_dir_css))
            local('cp dist/jquery.qtip.js {0}/'.format(dest_dir_js))
            local('cp dist/jquery.qtip.css {0}/'.format(dest_dir_css))


@recipe('jquery-ui-multiselect')
def install_jquery_ui_multiselect():
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
    dest_dir = os.path.join(lib_dir(env.src_dir, 'js'), 'mathjax/')
    mathjax_js = os.path.join(dest_dir, 'MathJax.js')

    with lcd(os.path.join(env.ext_dir, 'mathjax')):
        local('rm -rf {0}'.format(os.path.join(dest_dir)))
        _cp_tree('unpacked/', dest_dir, exclude=["AM*", "MML*", "Accessible*", "Safe*"])
        _cp_tree('fonts/', os.path.join(dest_dir, 'fonts'), exclude=["png"])

    with open(mathjax_js, 'r') as f:
        data = f.read()
        # Uncomment 'isPacked = true' line
        data = re.sub(r'//\s*(MathJax\.isPacked\s*=\s*true\s*;)', r'\1', data, re.MULTILINE)

    with open(mathjax_js, 'w') as f:
        f.write(data)


@recipe('PageDown')
def install_pagedown():
    with lcd(os.path.join(env.ext_dir, 'pagedown')):
        dest_dir = os.path.join(lib_dir(env.src_dir, 'js'), 'pagedown/')
        local('mkdir -p {0}'.format(dest_dir))
        local('cp *.js {0}'.format(dest_dir))


@recipe('clipboard.js')
def install_clipboard_js():
    """
    Install clipboard.js from Git
    """
    with lcd(os.path.join(env.ext_dir, 'clipboard.js')):
        dest_dir = os.path.join(lib_dir(env.src_dir, 'js'), 'clipboard.js/')
        local('mkdir -p {0}'.format(dest_dir))
        local('cp dist/clipboard.js {0}/'.format(dest_dir))


@recipe('dropzone.js')
def install_dropzone_js():
    """
    Install Dropzone from Git
    """
    with lcd(os.path.join(env.ext_dir, 'dropzone')):
        dest_js_dir = os.path.join(lib_dir(env.src_dir, 'js'), 'dropzone.js/')
        dest_css_dir = os.path.join(lib_dir(env.src_dir, 'css'), 'dropzone.js/')
        local('mkdir -p {0} {1}'.format(dest_js_dir, dest_css_dir))
        local('cp dist/dropzone.js {0}/'.format(dest_js_dir))
        local('cp dist/dropzone.css {0}/'.format(dest_css_dir))


@recipe('selectize.js')
def install_selectize_js():
    with lcd(os.path.join(env.ext_dir, 'selectize.js')):
        dest_js_dir = os.path.join(lib_dir(env.src_dir, 'js'), 'selectize.js/')
        dest_css_dir = os.path.join(lib_dir(env.src_dir, 'css'), 'selectize.js/')
        local('mkdir -p {0} {1}'.format(dest_js_dir, dest_css_dir))
        local('cp dist/js/standalone/selectize.js {0}/'.format(dest_js_dir))
        local('cp dist/css/selectize.css {0}/'.format(dest_css_dir))
        local('cp dist/css/selectize.default.css {0}/'.format(dest_css_dir))


@recipe('jquery-typeahead')
def install_jquery_typeahead():
    with lcd(os.path.join(env.ext_dir, 'jquery-typeahead')):
        dest_js_dir = lib_dir(env.src_dir, 'js')
        dest_css_dir = lib_dir(env.src_dir, 'css')
        local('mkdir -p {0} {1}'.format(dest_js_dir, dest_css_dir))
        local('cp src/jquery.typeahead.js {0}'.format(dest_js_dir))
        local('cp src/jquery.typeahead.css {0}'.format(dest_css_dir))


@recipe('jquery-tablesorter')
def install_jquery_tablesorter():
    with lcd(os.path.join(env.ext_dir, 'jquery-tablesorter')):
        dest_js_dir = lib_dir(env.src_dir, 'js')
        local('mkdir -p {0}'.format(dest_js_dir))
        local('cp dist/js/jquery.tablesorter.js {0}'.format(dest_js_dir))


@recipe('moment.js')
def install_moment_js():
    with lcd(os.path.join(env.ext_dir, 'moment.js')):
        dest_dir = os.path.join(lib_dir(env.src_dir, 'js'), 'moment.js')
        local('mkdir -p {0} {0}/locale'.format(dest_dir))

        local('cp moment.js {0}/'.format(dest_dir))
        local('cp locale/en-gb.js {0}/locale/'.format(dest_dir))
        local('cp locale/fr.js {0}/locale/'.format(dest_dir))
        local('cp locale/es.js {0}/locale/'.format(dest_dir))


@recipe('taggle.js')
def install_tagging_js():
    with lcd(os.path.join(env.ext_dir, 'taggle.js')):
        dest_js_dir = lib_dir(env.src_dir, 'js')
        local('mkdir -p {0}'.format(dest_js_dir))
        local('cp src/taggle.js {0}'.format(dest_js_dir))


@recipe('typewatch')
def install_typewatch():
    with lcd(os.path.join(env.ext_dir, 'typewatch')):
        dest_js_dir = lib_dir(env.src_dir, 'js')
        local('mkdir -p {}'.format(dest_js_dir))
        local('cp jquery.typewatch.js {}'.format(dest_js_dir))


@recipe('fullcalendar.js')
def install_fullcalendar_js():
    with node_env(), lcd(os.path.join(env.ext_dir, 'fullcalendar')):
        local('npm install')
        grunt('lumbar:build')
        dest_js_dir = lib_dir(env.src_dir, 'js')
        dest_css_dir = lib_dir(env.src_dir, 'css')
        local('mkdir -p {0}'.format(dest_js_dir))
        local('cp dist/fullcalendar.js {0}'.format(dest_js_dir))
        local('cp dist/fullcalendar.css {0}'.format(dest_css_dir))


@recipe('ckeditor')
def install_ckeditor():
    src_dir = os.path.join(env.ext_dir, 'ckeditor')
    dest_dir = os.path.join(lib_dir(env.src_dir, 'js'), 'ckeditor')
    with open(os.path.join(src_dir, 'build-config.js'), 'w') as f:
        f.write('var CKBUILDER_CONFIG = ')
        json.dump(CKBUILDER_CONFIG, f, indent=4, separators=(', ', ': '))
        f.write(';\n')
    with lcd(os.path.join(src_dir, 'dev', 'builder')):
        local('./build.sh --skip-omitted-in-build-config --no-zip --no-tar --build-config ../../build-config.js')
        with settings(warn_only=True):
            local('rm -rf {}'.format(dest_dir))
        local('mv release/ckeditor {}'.format(dest_dir))
    with lcd(dest_dir):
        local('rm -rf config.js bender.ci.js .travis.yml samples')


@recipe('outdated-browser')
def install_outdated_browser():
    with lcd(os.path.join(env.ext_dir, 'outdated-browser')):
        dest_js_dir = lib_dir(env.src_dir, 'js')
        dest_css_dir = lib_dir(env.src_dir, 'css')
        local('mkdir -p {0}'.format(dest_js_dir))
        local('cp outdatedbrowser/outdatedbrowser.js {0}'.format(dest_js_dir))
        local('cp outdatedbrowser/outdatedbrowser.css {0}'.format(dest_css_dir))


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
        local('git submodule init')
        local('git submodule sync')
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
    system_node = system_node.lower() in ('1', 'true') if system_node is not None else env.system_node

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
            local('npm install grunt-cli --prefix $(pwd)')

        _install_deps()


@task
def clean_deps(src_dir=None):
    """
    Clean up generated files
    """

    for dtype in ASSET_TYPES:
        _safe_rm('{0}/*'.format(lib_dir(src_dir or env.src_dir, dtype)), recursive=True)
