# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os

from indico.core.config import config


def validate_upload_file_size(*files):
    """Validate size of one or more uploaded files.

    Validation is done using the `MAX_UPLOAD_FILE_SIZE` config.
    """
    max_upload_file_size = config.MAX_UPLOAD_FILE_SIZE * 1024 * 1024
    if not max_upload_file_size:
        return True
    for file in files:
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        if file_size > max_upload_file_size:
            return False
    return True
