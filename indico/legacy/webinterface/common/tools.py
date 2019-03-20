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

from indico.core.logger import Logger


# Routine by Micah D. Cochran
# Submitted on 26 Aug 2005
# This routine is allowed to be put under any license Open Source (GPL, BSD, LGPL, etc.) License
# or any Propriety License. Effectively this routine is in public domain. Please attribute where appropriate.
def strip_ml_tags(in_text):
    """ Description: Removes all HTML/XML-like tags from the input text.
        Inputs: s --> string of text
        Outputs: text string without the tags

        # doctest unit testing framework

        >>> test_text = "Keep this Text <remove><me /> KEEP </remove> 123"
        >>> strip_ml_tags(test_text)
        'Keep this Text  KEEP  123'
    """

    # convert in_text to a mutable object (e.g. list)
    s_list = list(in_text)
    i = 0

    while i < len(s_list):
        # iterate until a left-angle bracket is found
        if s_list[i] == '<':
            try:
                while s_list[i] != '>':
                    # pop everything from the the left-angle bracket until the right-angle bracket
                    s_list.pop(i)
            except IndexError as e:
                Logger.get('strip_ml_tags').debug("Not found '>' (the end of the html tag): %s"%e)
                continue

            # pops the right-angle bracket, too
            s_list.pop(i)
        else:
            i=i+1

    # convert the list back into text
    join_char=''
    return join_char.join(s_list)
