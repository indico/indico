# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
import subprocess


def silent_check_call(*args, **kwargs):
    """Wrapper for `subprocess.check_call` which silences all output"""
    with open(os.devnull, 'w') as devnull:
        return subprocess.check_call(*args, stdout=devnull, stderr=devnull, **kwargs)
