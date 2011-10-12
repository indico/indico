# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from indico.util.contextManager import ContextManager


def request_cached(f):
    def _wrapper(*args, **kwargs):
        # if there are kwargs, skip caching
        if kwargs:
            return f(*args, **kwargs)
        else:
            # create a unique key
            k = (f, args)
            cache = ContextManager.setdefault('request_cache', {})
            if k not in cache:
                cache[k] = f(*args)
            return cache[k]
    return _wrapper


def order_dict(dict):
    """
    Very simple method that returns an sorted tuple of (k, v) tuples
    This is supposed to be used for converting shallow dicts into "hashable"
    values.
    """
    return tuple(sorted(dict.iteritems()))
