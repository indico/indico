# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

def isStringHTML(s):
    if not isinstance(s, str):
        return False
    s = s.lower()
    return any(tag in s for tag in ('<p>', '<p ', '<br', '<li>'))
