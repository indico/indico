import os
import re
import sys

from functools import wraps
from distutils.dist import Distribution
from distutils.cmd import Command as distutils_Command

from flask_script import Manager, Command, Option
from babel.messages import frontend

from pkgutil import walk_packages


IndicoI18nManager = Manager(usage="Takes care of i18n-related operations")

TRANSLATIONS_DIR = 'indico/translations'
MESSAGES_POT = os.path.join(TRANSLATIONS_DIR, 'messages.pot')
MESSAGES_JS_POT = os.path.join(TRANSLATIONS_DIR, 'messages-js.pot')

DEFAULT_OPTIONS = {
    'init_catalog': {
        'output_file': MESSAGES_POT,
        'output_dir': TRANSLATIONS_DIR
    },

    'extract_messages': {
        'keywords': 'N_:1,2',
        'width': 120,
        'output_file': MESSAGES_POT,
        'mapping_file': 'babel.cfg'
    },

    'compile_catalog': {
        'directory': TRANSLATIONS_DIR
    },

    'update_catalog': {
        'input_file': MESSAGES_POT,
        'output_dir': TRANSLATIONS_DIR
    },


    # JavaScript

    'init_catalog_js': {
        'output_file': MESSAGES_JS_POT,
        'output_dir': TRANSLATIONS_DIR,
        'domain': 'messages-js'
    },

    'extract_messages_js': {
        'keywords': '$T',
        'width': 120,
        'output_file': MESSAGES_JS_POT,
        'mapping_file': 'babel-js.cfg',
        'no_default_keywords': 1
    },

    'compile_catalog_js': {
        'input_dir': TRANSLATIONS_DIR,
        'output_dir': 'indico/htdocs/js/indico/i18n',
        'domain': 'messages-js'
    },

    'update_catalog_js': {
        'input_file': MESSAGES_JS_POT,
        'output_dir': TRANSLATIONS_DIR,
        'domain': 'messages-js'
    }
}


def find_packages(path, prefix=""):
    yield prefix
    prefix = prefix + "."
    for _, name, ispkg in walk_packages(path, prefix):
        if ispkg:
            yield name


def wrap_distutils_command(command_class):
    @wraps(command_class)
    def _wrapper(**kwargs):

        from MaKaC import __version__
        import indico

        command = command_class(Distribution({
            'name': 'indico',
            'version': __version__,
            'packages': find_packages(indico.__path__, indico.__name__)
            }))

        for key, val in kwargs.items():
            setattr(command, key, val)

        command.finalize_options()
        command.run()

    return _wrapper


class compile_catalog_js(distutils_Command):
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
        import pkg_resources
        try:
            pkg_resources.require('pojson')
        except pkg_resources.DistributionNotFound:
            print """
            pojson not found! pojson is needed for JS i18n file generation.
            If you're building Indico from source. Please install it.
            i.e. try 'easy_install pojson'"""
            sys.exit(-1)

        from pojson import convert

        localeDirs = [name for name in os.listdir(self.input_dir) if os.path.isdir(os.path.join(self.input_dir, name))]

        for locale in localeDirs:
            result = convert(os.path.join(
                self.input_dir, locale, "LC_MESSAGES", 'messages-js.po'), pretty_print=True)
            fname = os.path.join(self.output_dir, '%s.js' % locale)
            with open(fname, 'w') as f:
                f.write((u"var json_locale_data = {0};".format(result)).encode('utf-8'))
            print 'wrote %s' % fname


cmd_list = ['init_catalog', 'extract_messages', 'compile_catalog', 'update_catalog']
cmd_list += [cmd + '_js' for cmd in cmd_list]

for cmd in cmd_list:
    cmd_class = compile_catalog_js if cmd == 'compile_catalog_js' else getattr(frontend, re.sub(r'_js$', '', cmd))

    command = Command(wrap_distutils_command(cmd_class))

    for opt, short_opt, description in cmd_class.user_options:

        long_opt_name = opt.rstrip('=')
        var_name = long_opt_name.replace('-', '_')
        opts = ['--' + long_opt_name]

        if short_opt:
            opts.append('-' + short_opt)

        command.add_option(Option(*opts, dest=var_name,
                                  action=(None if opt.endswith('=') else 'store_true'), help=description,
                                  default=DEFAULT_OPTIONS.get(cmd, {}).get(var_name)))

    IndicoI18nManager.add_command(cmd, command)
