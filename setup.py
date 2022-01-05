# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import json
import os
import subprocess
from distutils.command.build import build

from setuptools import setup


def read_requirements_file(fname):
    with open(fname) as f:
        return [dep for d in f.readlines() if (dep := d.strip()) and not (dep.startswith(('-', '#')) or '://' in dep)]


def get_requirements(fname):
    return read_requirements_file(os.path.join(os.path.dirname(__file__), fname))


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
        cmdclass=cmdclass,
        install_requires=get_requirements('requirements.txt'),
        extras_require={'dev': get_requirements('requirements.dev.txt')},
    )
