# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.attachments.controllers.display.base import DownloadAttachmentMixin
from indico.modules.categories.controllers.base import RHDisplayCategoryBase


class RHDownloadCategoryAttachment(DownloadAttachmentMixin, RHDisplayCategoryBase):
    def _process_args(self):
        RHDisplayCategoryBase._process_args(self)
        DownloadAttachmentMixin._process_args(self)
