# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import ast
import json
import os
import re
import subprocess
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

    def _compile_languages_react(self):
        for locale in os.listdir('indico/translations'):
            po_file = os.path.join('indico/translations', locale, 'LC_MESSAGES', 'messages-react.po')
            json_file = os.path.join('indico/translations', locale, 'LC_MESSAGES', 'messages-react.json')
            if not os.path.exists(po_file):
                continue
            with open(os.devnull, 'w') as devnull:
                output = subprocess.check_output(['npx', 'react-jsx-i18n', 'compile', po_file], stderr=devnull)
            json.loads(output)  # just to be sure the JSON is valid
            with open(json_file, 'wb') as f:
                f.write(output)

    def run(self):
        self._compile_languages()
        self._compile_languages_react()
        build.run(self)


cmdclass = {}
if os.environ.get('READTHEDOCS') != 'True':
    cmdclass = {'build': BuildWithTranslations}


if __name__ == '__main__':
    setup(
        name='indico',
        version=get_version(),
        cmdclass=cmdclass,
        description='Indico is a full-featured conference lifecycle management and meeting/lecture scheduling tool',
        long_description_content_type='text/markdown',
        author='Indico Team',
        author_email='indico-team@cern.ch',
        url='https://getindico.io',
        download_url='https://github.com/indico/indico/releases',
        long_description="Indico allows you to schedule conferences, from single talks to complex meetings with "
                         "sessions and contributions. It also includes an advanced user delegation mechanism, "
                         "allows paper reviewing, archival of conference information and electronic proceedings",
        license='MIT',
        zip_safe=False,
        packages=find_packages(include=('indico', 'indico.*',)),
        include_package_data=True,
        install_requires=get_requirements(),
        python_requires='~=3.9',
        classifiers=[
            'Environment :: Web Environment',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 3.9',
        ],
        entry_points={
            'console_scripts': {'indico = indico.cli.core:cli'},
            'celery.commands': {'unlock = indico.core.celery.cli:UnlockCommand'},
            'pytest11': {'indico = indico.testing.pytest_plugin'},
        })
