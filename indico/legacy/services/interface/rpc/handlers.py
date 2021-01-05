# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from importlib import import_module


methodMap = {}
endpointMap = {
    "search": import_module('indico.legacy.services.implementation.search')
}
