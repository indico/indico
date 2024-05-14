# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import subprocess


def silent_check_call(*args, **kwargs):
    """Wrapper for `subprocess.check_call` which silences all output."""
    return subprocess.check_call(*args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kwargs)
