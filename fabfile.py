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
import requests
import json
import getpass
from contextlib import contextmanager
import requests_pyopenssl
from requests.packages.urllib3 import connectionpool
connectionpool.ssl_wrap_socket = requests_pyopenssl.ssl_wrap_socket
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

env.conf = 'fabfile.conf'
env.src_dir = os.path.dirname(__file__)
execfile(env.conf, {}, env)
env.build_dir = os.path.join(env.src_dir, env.build_dirname)
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

    if not os.path.isdir(env.pyenv_dir):
        print red("Can't find pyenv!")
        print yellow("Are you sure you have installed it?")
        sys.exit(-2)
    elif not os.path.isdir(os.path.join(env.pyenv_dir, 'plugins', 'pyenv-virtualenv')):
        print red("Can't find pyenv-virtualenv!")
        print yellow("Are you sure you have installed it?")
        sys.exit(-2)

    # list available pythonbrew versions
    av_versions = list(entry.strip() for entry in pyenv_cmd('versions', capture=True).split('\n')[1:])

    for py_version in py_versions:
        if (py_version) not in av_versions:
            print green('Installing Python {0}'.format(py_version))
            pyenv_cmd('install {0}'.format(py_version), capture=True)

        local("echo \'y\' | pyenv virtualenv {0} indico-build-{0}".format(py_version))


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
        local('{0} -q install {1} --allow-all-external -r requirements.txt'
              .format(os.path.join(cmd_dir, 'pip'),
                      ' '.join("--allow-unverified {0}".format(pkg) for pkg in env.unverified)))
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
        print red("ERROR: {0}".format(msg))
        sys.exit(-2)


def _valid_github_credentials(auth):
    url = "https://api.github.com/repos/{0}/{1}".format(env.github['usr'], env.github['repo'])
    r = requests.get(url, auth=(env.github['usr'], auth))
    if (r.status_code == 401) and (r.json().get('message') == 'Bad credentials'):
        print red('Invalid Github credentials for user \'{0}\''.format(env.github['usr']))
        return False

    return True


def _release_exist(tag_name, auth):
    url = "https://api.github.com/repos/{0}/{1}/releases".format(env.github['usr'], env.github['repo'])
    r = requests.get(url, auth=(env.github['usr'], auth))
    _check_request_error(r)
    parsed = r.json()
    for j in parsed:
        if j.get('tag_name') == tag_name:
            rel_id = j.get('id')
            return (True, rel_id)

    return (False, 0)


def _asset_exist(rel_id, name, auth):
    url = "https://api.github.com/repos/{0}/{1}/releases/{2}/assets" \
          .format(env.github['usr'], env.github['repo'], rel_id)
    r = requests.get(url, auth=(env.github['usr'], auth))
    _check_request_error(r)
    parsed = r.json()
    for j in parsed:
        if j.get('name') == name:
            asset_id = j.get('id')
            return (True, asset_id)

    return (False, 0)


def _upload_github(build_dir, indico_version, tag_name, auth, overwrite):

    auth = auth or env.github['auth']
    while (auth is None) or (not _valid_github_credentials(auth)):
        auth = getpass.getpass('Insert the Github password/OAuth token for user \'{0}\': '.format(env.github['usr']))

    overwrite = overwrite or env.github['overwrite']

    # Create a new release
    tag_name = tag_name or indico_version
    url = "https://api.github.com/repos/{0}/{1}/releases".format(env.github['usr'], env.github['repo'])
    payload = {'tag_name': tag_name}
    (exist, rel_id) = _release_exist(tag_name, auth)
    if exist and overwrite is None:
        overwrite = _yes_no_input('Release already exists, do you want to overwrite', 'n')

    if not exist:
        r = requests.post(url, auth=(env.github['usr'], auth), data=json.dumps(payload))
        _check_request_error(r)
        release_id = r.json().get('id')
    elif exist and overwrite:
        release_id = rel_id
    elif exist and not overwrite:
        return

    # Upload binaries to the new release
    binaries_dir = os.path.join(build_dir, 'indico', 'dist')
    url = "https://uploads.github.com/repos/{0}/{1}/releases/{2}/assets" \
          .format(env.github['usr'], env.github['repo'], release_id)
    for f in os.listdir(binaries_dir):
        if os.path.isfile(os.path.join(binaries_dir, f)):
            (exist, asset_id) = _asset_exist(release_id, f, auth)

            if exist:
                del_url = "https://api.github.com/repos/{0}/{1}/releases/assets/{2}" \
                          .format(env.github['usr'], env.github['repo'], asset_id)
                r = requests.delete(del_url, auth=(env.github['usr'], auth))
                _check_request_error(r)

            with open(os.path.join(binaries_dir, f), 'rb') as ff:
                data = ff.read()
                extension = os.path.splitext(f)[1]
                if extension == '.gz':
                    headers = {'Content-Type': 'application/x-gzip'}
                elif extension == '.egg':
                    headers = {'Content-Type': 'application/zip'}
                headers['Accept'] = 'application/vnd.github.v3+json'
                headers['Content-Length'] = len(data)
                params = {'name': f}

                print green("Uploading \'{0}\' to Github".format(f))
                r = requests.post(url, auth=(env.github['usr'], auth), headers=headers, data=data, params=params)
                _check_request_error(r)


def _upload_server(build_dir, server_name, server_port, ssh_key, dest_dir):
    env.hosts = [env.server['name']+':'+env.server['port']]
    env.user = env.server['usr']
    env.key_filename = env.server['key']

    binaries_dir = os.path.join(build_dir, 'indico', 'dist')
    for f in os.listdir(binaries_dir):
        if os.path.isfile(os.path.join(binaries_dir, f)):
            _putl(os.path.join(binaries_dir, f), dest_dir)


@task
def package_release(py_versions=None, build_dir=None, system_node=False,
                    indico_versions=None, upstream=None, tag_name=None,
                    git_auth=None, overwrite=None, server_name=None,
                    server_port=None, ssh_key=None, dest_dir=None,
                    no_clean=False, force_clean=False, *upload_to):
    """
    Create an Indico release - source and binary distributions
    """

    DEVELOP_REQUIRES = ['pojson>=0.4', 'termcolor', 'werkzeug', 'nodeenv', 'fabric',
                        'sphinx', 'repoze.sphinx.autointerface']

    py_versions = py_versions.split('/') if py_versions else env.py_versions
    build_dir = build_dir or env.build_dir
    upstream = upstream or env.github['upstream']
    indico_versions = indico_versions or env.indico_versions

    if not upload_to:
        upload_to = ['github', 'server']

    local('mkdir -p {0}'.format(build_dir))

    if not no_clean:
        if not force_clean and not console.confirm(red("This will reset your repository to its initial "
            "state (you will lose all files that are not under Git version control). Do you want to continue?"),
            default=False):
            sys.exit(2)

        local('git clean -dx')

    with pyenv_env(py_versions[-1]):
        local('pip -q install {0}'.format(' '.join(DEVELOP_REQUIRES + ['babel'])))


    _check_pyenv(py_versions)


    with lcd(build_dir):
        # Clone this same repo
        if os.path.exists(os.path.join(build_dir, 'indico')):
            print yellow("Repository seems to already exist.")
            with lcd('indico'):
                local('git fetch {0}'.format(upstream))
                local('git reset --hard FETCH_HEAD')
                local('git clean -df')
        else:
            local('git clone {0}'.format(upstream))
        with lcd('indico'):
            for indico_version in indico_versions:
                print green("Checking out branch \'{0}\'".format(indico_version))
                local('git checkout origin/{0}'.format(indico_version))

                # Build source tarball
                with settings(system_node=system_node):
                    print green('Generating '), cyan('tarball')
                    tarball(os.path.join(build_dir, 'indico'))

                # Build binaries (EGG)
                print green('Generating '), cyan('eggs')
                egg(py_versions)

                for u in upload_to:
                    if u == 'github':
                        _upload_github(build_dir, indico_version, tag_name, git_auth, overwrite)
                    elif u == 'server':
                        _upload_server(build_dir, server_name, server_port, ssh_key, dest_dir)

    cleanup(build_dir, force=True)
