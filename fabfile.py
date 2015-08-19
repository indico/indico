# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

import os
import re
import sys
import glob
import shutil
import requests
import json
import getpass
from contextlib import contextmanager
import operator

from fabric.api import local, lcd, task, env
from fabric.context_managers import prefix, settings
from fabric.colors import red, green, yellow, cyan
from fabric.contrib import console
from fabric.operations import put, run


ASSET_TYPES = ['js', 'sass', 'css']
DOC_DIRS = ['guides']
RECIPES = {}
DEFAULT_REQUEST_ERROR_MSG = 'UNDEFINED ERROR (no error description from server)'
CONF_FILE_NAME = 'fabfile.conf'
SOURCE_DIR = os.path.dirname(__file__)

execfile(CONF_FILE_NAME, {}, env)

env.update({
    'conf': CONF_FILE_NAME,
    'src_dir': SOURCE_DIR,
    'ext_dir': os.path.join(SOURCE_DIR, env.ext_dirname),
    'target_dir': os.path.join(SOURCE_DIR, env.target_dirname),
    'node_env_path': os.path.join(SOURCE_DIR, env.node_env_dirname)
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


@contextmanager
def pyenv_env(version):
    cmd_dir = os.path.join(env.pyenv_dir, 'versions', 'indico-build-{0}'.format(version), 'bin')
    with prefix('PATH={0}:$PATH'.format(cmd_dir)):
        yield


def pyenv_cmd(cmd, **kwargs):
    cmd_dir = os.path.join(env.pyenv_dir, 'bin')
    return local('{0}/pyenv {1}'.format(cmd_dir, cmd), **kwargs)


# Util functions

def _yes_no_input(message, default):
    c = '? '
    if default.lower() == 'y':
        c = ' [Y/n]? '
    elif default.lower() == 'n':
        c = ' [y/N]? '
    s = raw_input(message+c) or default
    if s.lower() == 'y':
        return True
    else:
        return False


def _putl(source_file, dest_dir):
    """
    To be used instead of put, since it doesn't support symbolic links
    """

    put(source_file, '/')
    run("mkdir -p {0}".format(dest_dir))
    run("mv -f /{0} {1}".format(os.path.basename(source_file), dest_dir))


def create_node_env():
    with settings(warn_only=True):
        local('nodeenv -c -n {0} {1}'.format(env.node_version, env.node_env_path))


def lib_dir(src_dir, dtype):
    target_dir = os.path.join(src_dir, 'indico', 'htdocs')
    return os.path.join(target_dir, dtype, 'lib')


def _check_pyenv(py_versions):
    """
    Check that pyenv and pyenv-virtualenv are installed and set up the
    compilers/virtual envs in case they do not exist
    """

    if os.system('which pyenv'):
        print red("Can't find pyenv!")
        print yellow("Are you sure you have installed it?")
        sys.exit(-2)
    elif os.system('which pyenv-virtualenv'):
        print red("Can't find pyenv-virtualenv!")
        print yellow("Are you sure you have installed it?")
        sys.exit(-2)

    # list available pyenv versions
    av_versions = os.listdir(os.path.join(env.pyenv_dir, 'versions'))

    for py_version in py_versions:
        if py_version not in av_versions:
            print green('Installing Python {0}'.format(py_version))
            pyenv_cmd('install {0}'.format(py_version), capture=True)

        local("echo \'y\' | pyenv virtualenv {0} indico-build-{0}".format(py_version))

        with pyenv_env(py_version):
            local("pip install -r requirements.dev.txt")


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


def _find_most_recent(path, cmp=operator.gt, maxt=0):
    for dirpath, __, fnames in os.walk(path):
        for fname in fnames:

            # ignore hidden files and ODTs
            if fname.startswith(".") or fname.endswith(".odt"):
                continue

            mtime = os.stat(os.path.join(dirpath, fname)).st_mtime
            if cmp(mtime, maxt):
                maxt = mtime
    return maxt


def _find_least_recent(path):
    return _find_most_recent(path, cmp=operator.lt, maxt=sys.maxint)


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
            local('grunt clean buildall copy write compress')
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
            local('grunt')
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
            local('grunt --plugins="tips modal viewport svg" init clean concat:dist concat:css concat:libs replace')
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
    with lcd(os.path.join(env.ext_dir, 'pagedown')):
        dest_dir = os.path.join(lib_dir(env.src_dir, 'js'), 'pagedown/')
        local('mkdir -p {0}'.format(dest_dir))
        local('cp *.js {0}'.format(dest_dir))


@recipe('ZeroClipboard')
def install_zeroclipboard():
    """
    Install ZeroClipboard from Git
    """
    with lcd(os.path.join(env.ext_dir, 'zeroclipboard')):
        dest_dir = os.path.join(lib_dir(env.src_dir, 'js'), 'zeroclipboard/')
        local('mkdir -p {0}'.format(dest_dir))
        local('cp dist/ZeroClipboard.js {0}/'.format(dest_dir))
        local('cp dist/ZeroClipboard.swf {0}/'.format(dest_dir))


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
    Create a source Indico distribution (tarball)
    """

    src_dir = src_dir or env.src_dir

    make_docs(src_dir)

    setup_deps(n_env=os.path.join(src_dir, 'ext_modules', 'node_env'),
               src_dir=src_dir)
    local('python setup.py -q sdist')


@task
def egg(py_versions=None):
    """
    Create a binary Indico distribution (egg)
    """

    for py_version in py_versions:
        cmd_dir = os.path.join(env.pyenv_dir, 'versions', 'indico-build-{0}'.format(py_version), 'bin')
        local('{0} setup.py -q bdist_egg'.format(os.path.join(cmd_dir, 'python')))
    print green(local('ls -lah dist/', capture=True))


@task
def make_docs(src_dir=None, build_dir=None, force=False):
    """
    Generate Indico docs
    """

    src_dir = src_dir or env.src_dir
    doc_src_dir = os.path.join(src_dir, 'doc')

    if build_dir is None:
        target_dir = os.path.join(src_dir, 'indico', 'htdocs', 'ihelp')
    else:
        target_dir = os.path.join(build_dir or env.build_dir, 'indico', 'htdocs', 'ihelp')

    if not force:
        print yellow("Checking if docs need to be generated... "),
        if _find_most_recent(target_dir) > _find_most_recent(doc_src_dir):
            print green("Nope.")
            return

    print red("Yes :(")
    _check_present('pdflatex')

    print green('Generating documentation')
    with lcd(doc_src_dir):
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


def _check_request_error(r):
    if r.status_code >= 400:
        j = r.json()
        msg = j.get('message', DEFAULT_REQUEST_ERROR_MSG)
        print red("ERROR: {0} ({1})".format(msg, r.status_code))
        sys.exit(-2)


def _valid_github_credentials(auth):
    url = "https://api.github.com/repos/{0}/{1}".format(env.github['org'], env.github['repo'])
    r = requests.get(url, auth=(env.github['user'], auth))
    if (r.status_code == 401) and (r.json().get('message') == 'Bad credentials'):
        print red('Invalid Github credentials for user \'{0}\''.format(env.github['user']))
        return False

    return True


def _release_exists(tag_name, auth):
    url = "https://api.github.com/repos/{0}/{1}/releases".format(env.github['org'], env.github['repo'])
    r = requests.get(url, auth=(env.github['user'], auth))
    _check_request_error(r)
    parsed = r.json()
    for release in parsed:
        if release.get('tag_name') == tag_name:
            rel_id = release.get('id')
            return (True, rel_id, release)

    return (False, 0, None)


def _asset_exists(rel_id, name, auth):
    url = "https://api.github.com/repos/{0}/{1}/releases/{2}/assets" \
          .format(env.github['org'], env.github['repo'], rel_id)
    r = requests.get(url, auth=(env.github['user'], auth))
    _check_request_error(r)
    parsed = r.json()
    for j in parsed:
        if j.get('name') == name:
            asset_id = j.get('id')
            return (True, asset_id)

    return (False, 0)


@task
def upload_github(build_dir=None, tag_name=None, auth_token=None,
                  overwrite=None, indico_version='master'):

    build_dir = build_dir or env.build_dir
    auth_token = auth_token or env.github['auth_token']

    while (auth_token is None) or (not _valid_github_credentials(auth_token)):
        auth_token = getpass.getpass(
            'Insert the Github password/OAuth token for user \'{0}\': '.format(env.github['user']))

    auth_creds = (env.github['user'], auth_token)

    overwrite = overwrite or env.github['overwrite']

    # Create a new release
    tag_name = tag_name or indico_version
    url = "https://api.github.com/repos/{0}/{1}/releases".format(env.github['org'], env.github['repo'])
    payload = {
        'tag_name': tag_name,
        'target_commitish': indico_version,
        'name': 'Indico {0}'.format(tag_name),
        'draft': True
    }

    (exists, rel_id, release_data) = _release_exists(tag_name, auth_token)

    if exists:
        if overwrite is None:
            overwrite = _yes_no_input('Release already exists, do you want to overwrite', 'n')
        if overwrite:
            release_id = rel_id
        else:
            return
    else:
        # We will need to get a new release id from github
        r = requests.post(url, auth=auth_creds, data=json.dumps(payload))
        _check_request_error(r)
        release_data = r.json()
        release_id = release_data.get('id')

    # Upload binaries to the new release
    binaries_dir = os.path.join(build_dir, 'indico', 'dist')

    # awful way to handle this, but a regex seems like too much
    url = release_data['upload_url'][:-7]

    for f in os.listdir(binaries_dir):

        # jump over hidden/system files
        if f.startswith('.'):
            continue

        if os.path.isfile(os.path.join(binaries_dir, f)):
            (exists, asset_id) = _asset_exists(release_id, f, auth_token)

            if exists:
                # delete previous version
                del_url = "https://api.github.com/repos/{0}/{1}/releases/assets/{2}" \
                          .format(env.github['org'], env.github['repo'], asset_id)
                r = requests.delete(del_url, auth=auth_creds)
                _check_request_error(r)

            with open(os.path.join(binaries_dir, f), 'rb') as ff:
                data = ff.read()
                extension = os.path.splitext(f)[1]

                # upload eggs using zip mime type
                if extension == '.gz':
                    headers = {'Content-Type': 'application/x-gzip'}
                elif extension == '.egg':
                    headers = {'Content-Type': 'application/zip'}

                headers['Accept'] = 'application/vnd.github.v3+json'
                headers['Content-Length'] = len(data)
                params = {'name': f}

                print green("Uploading \'{0}\' to Github".format(f))
                r = requests.post(url, auth=auth_creds, headers=headers, data=data, params=params, verify=False)
                _check_request_error(r)


@task
def upload_ssh(build_dir=None, server_host=None, server_port=None,
               ssh_user=None, ssh_key=None, dest_dir=None):

    build_dir = build_dir or env.build_dir
    server_host = server_host or env.ssh['host']
    server_port = server_port or env.ssh['port']
    ssh_user = ssh_user or env.ssh['user']
    ssh_key = ssh_key or env.ssh['key']
    dest_dir = dest_dir or env.ssh['dest_dir']

    env.host_string = server_host + ':' + server_port
    env.user = ssh_user
    env.key_filename = ssh_key

    binaries_dir = os.path.join(build_dir, 'indico', 'dist')
    for f in os.listdir(binaries_dir):
        if os.path.isfile(os.path.join(binaries_dir, f)):
            _putl(os.path.join(binaries_dir, f), dest_dir)


@task
def _package_release(build_dir, py_versions, system_node):
    # Build source tarball
    with settings(system_node=system_node):
        print green('Generating '), cyan('tarball')
        tarball(build_dir)

    # Build binaries (EGG)
    print green('Generating '), cyan('eggs')
    egg(py_versions)


@task
def package_release(py_versions=None, build_dir=None, system_node=False,
                    indico_version=None, upstream=None, tag_name=None,
                    github_auth=None, overwrite=None, ssh_server_host=None,
                    ssh_server_port=None, ssh_user=None, ssh_key=None,
                    ssh_dest_dir=None, no_clean=False, force_clean=False,
                    upload_to=None, build_here=False):
    """
    Create an Indico release - source and binary distributions
    """

    DEVELOP_REQUIRES = ['pojson>=0.4', 'termcolor', 'werkzeug', 'nodeenv', 'fabric',
                        'sphinx', 'repoze.sphinx.autointerface']

    py_versions = py_versions.split('/') if py_versions else env.py_versions
    upload_to = upload_to.split('/') if upload_to else []

    build_dir = build_dir or env.build_dir
    upstream = upstream or env.github['upstream']

    ssh_server_host = ssh_server_host or env.ssh['host']
    ssh_server_port = ssh_server_port or env.ssh['port']
    ssh_user = ssh_user or env.ssh['user']
    ssh_key = ssh_key or env.ssh['key']
    ssh_dest_dir = ssh_dest_dir or env.ssh['dest_dir']

    indico_version = indico_version or 'master'

    local('mkdir -p {0}'.format(build_dir))

    _check_pyenv(py_versions)

    if build_here:
        _package_release(os.path.dirname(__file__), py_versions, system_node)
    else:
        with lcd(build_dir):
            if os.path.exists(os.path.join(build_dir, 'indico')):
                print yellow("Repository seems to already exist.")
                with lcd('indico'):
                    local('git fetch {0}'.format(upstream))
                    local('git reset --hard FETCH_HEAD')
                    if not no_clean:
                        local('git clean -df')
            else:
                local('git clone {0}'.format(upstream))
            with lcd('indico'):
                print green("Checking out branch \'{0}\'".format(indico_version))
                local('git checkout {0}'.format(indico_version))

                _package_release(os.path.join(build_dir, 'indico'), py_versions, system_node)

    for u in upload_to:
        if u == 'github':
            upload_github(build_dir, tag_name, github_auth, overwrite, indico_version)
        elif u == 'ssh':
            upload_ssh(build_dir, ssh_server_host, ssh_server_port, ssh_user, ssh_key, ssh_dest_dir)

    if not build_here and force_clean:
        cleanup(build_dir, force=True)
