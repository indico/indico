# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

import hashlib
import os
import re
import stat
import sys

MATCH_PYTHON_BLOCK = re.compile('<%.*?%>', re.DOTALL)
MATCH_FORMAT = re.compile('%\(([^)]+)\)s')
MATCH_DECLARE_NEW = re.compile('<%\s*declareTemplate\(newTemplateStyle\s*=\s*True\)\s*%>\n*')

def sha1(data):
    h = hashlib.sha1()
    h.update(data)
    return h.hexdigest()

def fix_template(path):
    print "Fixing %s..." % path,
    f = open(path, 'rb')
    template = '\n'.join(line.rstrip() for line in f)
    f.close()

    stored_blocks = {}
    def replace_blocks(m):
        block = m.group(0)
        block_hash = sha1(block)
        stored_blocks[block_hash] = block
        return '{{{%s}}}' % block_hash

    num_converted = [0] # list so we can modify it from inside the callback
    def convert_variables(m):
        name = m.group(1)
        num_converted[0] += 1
        return '<%%= %s %%>' % name

    def fix_if_syntax(tpl):
        """Fix <% if expr: %>..<%%> to <% if expr: %>..<% end %>.
        This is needed so we can do the replacement of %% to % later.
        """
        inline_if = r"""
        (?P<if_construct>
        <%\s*if\s+
            (?:(?!<%|%>).)* # Matches strings not containing <% or %>
        :\s*%>
            (?:(?!<%|%>).)* # Matches strings not containing <% or %>
        )
        <%%>
        """
        prog = re.compile(inline_if, re.VERBOSE)
        return prog.sub(r'\g<if_construct><% end %>', tpl)

    fixed = fix_if_syntax(template)

    fixed = MATCH_DECLARE_NEW.sub('', fixed)
    fixed = MATCH_PYTHON_BLOCK.sub(replace_blocks, fixed)
    fixed = MATCH_FORMAT.sub(convert_variables, fixed)

    fixed = fixed.replace('%%', '%')

    for key, block in stored_blocks.iteritems():
        fixed = fixed.replace('{{{%s}}}' % key, block)

    if fixed == template:
        print ' nothing to do'
    else:
        print ' done [%d]' % num_converted[0]
        f = open(path, 'wb')
        f.write(fixed)
        f.close()


def walktree(top='.'):
    names = os.listdir(top)
    yield top, names
    for name in names:
        try:
            st = os.lstat(os.path.join(top, name))
        except os.error:
            continue
        if stat.S_ISDIR(st.st_mode):
            for newtop, children in walktree(os.path.join(top, name)):
                yield newtop, children

for basepath, children in walktree('cds-indico'):
    for child in children:
        if child.endswith('.tpl'):
            fix_template(os.path.join(basepath, child))
