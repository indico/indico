# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from PIL import EpsImagePlugin

from indico.util.mimetypes import register_custom_mimetypes
from indico.util.network import patch_socket_getaddrinfo


__version__ = '3.3.14-dev'
PREFERRED_PYTHON_VERSION_SPEC = '~=3.12.2'

register_custom_mimetypes()
patch_socket_getaddrinfo()

# We don't expect to ever process EPS files (since we check the image type against a whitelist),
# but just for added security we explicitly tell Pillow that it cannot call GhostScript. This is
# done by weasyprint as well, but it's cleaner to modify the global state early on instead of letting
# another library do it while it's being imported.
EpsImagePlugin.gs_binary = False
