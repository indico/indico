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

from __future__ import unicode_literals

import ast
import os
import re
from distutils.command.build import build

from setuptools import find_packages, setup


def read_requirements_file(fname):
    with open(fname, 'r') as f:
        return [dep.strip() for dep in f.readlines() if not (dep.startswith('-') or '://' in dep)]


def get_requirements():
    return read_requirements_file(os.path.join(os.path.dirname(__file__), 'requirements.txt'))


def get_version():
    _version_re = re.compile(r'__version__\s+=\s+(.*)')
    with open('indico/__init__.py', 'rb') as f:
        return str(ast.literal_eval(_version_re.search(f.read().decode('utf-8')).group(1)))


class BuildWithTranslations(build):
    def _compile_languages(self):
        from babel.messages import frontend
        compile_cmd = frontend.compile_catalog(self.distribution)
        self.distribution._set_command_options(compile_cmd)
        compile_cmd.finalize_options()
        compile_cmd.run()

    def run(self):
        self._compile_languages()
        build.run(self)


if __name__ == '__main__':
    setup(
        name='indico',
        version=get_version(),
        cmdclass={'build': BuildWithTranslations},
        description='Indico is a full-featured conference lifecycle management and meeting/lecture scheduling tool',
        author='Indico Team',
        author_email='indico-team@cern.ch',
        url='https://getindico.io',
        download_url='https://github.com/indico/indico/releases',
        long_description="Indico allows you to schedule conferences, from single talks to complex meetings with "
                         "sessions and contributions. It also includes an advanced user delegation mechanism, "
                         "allows paper reviewing, archival of conference information and electronic proceedings",
        license='https://www.gnu.org/licenses/gpl-3.0.txt',
        zip_safe=False,
        packages=find_packages(include=('indico', 'indico.*',)),
        include_package_data=True,
        install_requires=get_requirements(),
        entry_points={
            'console_scripts': {'indico = indico.cli.core:cli'},
            'celery.commands': {'unlock = indico.core.celery.cli:UnlockCommand'},
            'pytest11': {'indico = indico.testing.pytest_plugin'},
        })
