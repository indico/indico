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
Utility functions used by Indico's setup process.
This should normally not require anything that we can suppose that will be
available to the setup script before any configuration is done (e.g. flask)
"""


import os
import pojson
from distutils.cmd import Command


class compile_catalog_js(Command):
    """
    Translates *.po files to a JSON dict, with a little help from pojson
    """

    description = "generates JSON from po"
    user_options = [('input-dir=', None, 'input dir'),
                    ('output-dir=', None, 'output dir'),
                    ('domain=', None, 'domain')]
    boolean_options = []

    def initialize_options(self):
        self.input_dir = None
        self.output_dir = None
        self.domain = None

    def finalize_options(self):
        pass

    def run(self):
        locale_dirs = [name for name in os.listdir(self.input_dir) if os.path.isdir(os.path.join(self.input_dir, name))]

        for locale in locale_dirs:
            result = pojson.convert(os.path.join(
                self.input_dir, locale, "LC_MESSAGES", 'messages-js.po'), pretty_print=True)
            fname = os.path.join(self.output_dir, '%s.js' % locale)
            with open(fname, 'w') as f:
                f.write((u"var json_locale_data = {0};".format(result)).encode('utf-8'))
            print 'wrote %s' % fname
