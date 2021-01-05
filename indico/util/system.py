# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import platform

import distro


def get_os():
    if distro_info := f'{distro.name()} {distro.version()}'.strip():
        return distro_info
    # fallback for non-linux/bsd systems (ie mac os)
    return f'{platform.system()} {platform.release()}'.strip()
