# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import dataclasses

from markupsafe import Markup


@dataclasses.dataclass(frozen=True)
class RegistrationListColumn:
    #: The content of the cell (``<td>`` element`)
    content: str | Markup
    #: The text value of the cell (``data-text``)
    text_value: str
    #: Additional HTML attributes of the cell
    td_attrs: dict = dataclasses.field(default_factory=dict)
