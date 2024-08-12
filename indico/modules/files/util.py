# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os

from indico.core.config import config


def validate_upload_file_size(files, multiple=False):
    """Validate size of one or more uploaded files.

    Validation is done using the `MAX_UPLOAD_FILE_SIZE` and `MAX_UPLOAD_FILES_TOTAL_SIZE` config.
    """
    if not multiple:
        files = [files]
    max_upload_files_total_size = config.MAX_UPLOAD_FILES_TOTAL_SIZE * 1024 * 1024
    max_upload_file_size = config.MAX_UPLOAD_FILE_SIZE * 1024 * 1024
    if max_upload_files_total_size == 0 and max_upload_file_size == 0:
        return True
    total_file_size = 0
    for file in files:
        file_size = os.fstat(file.fileno()).st_size
        if max_upload_file_size != 0 and file_size > max_upload_file_size:
            return False
        total_file_size += file_size
        if max_upload_files_total_size != 0 and total_file_size > max_upload_files_total_size:
            return False
    return True
