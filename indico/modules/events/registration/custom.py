# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import dataclasses

from markupsafe import Markup

from indico.modules.events.registration.models.registrations import Registration


@dataclasses.dataclass(frozen=True)
class RegistrationListColumn:
    #: The content of the cell (``<td>`` element`)
    content: str | Markup
    #: The text value of the cell (``data-text``)
    text_value: str
    #: Additional HTML attributes of the cell
    td_attrs: dict = dataclasses.field(default_factory=dict)


class CustomRegistrationListItem:
    #: The (globally unique) name of the custom item
    name = None
    #: The title of the custom item
    title = None
    #: Whether the item is only used for filtering and does not display a column
    filter_only = False

    def __init__(self, event, regform):
        self.event = event
        self.regform = regform
        self.data: dict[Registration, RegistrationListColumn] = None  # assigned outside

    @property
    def filter_choices(self) -> dict:
        """A dict of options to choose if the item can be used for filtering."""
        return {}

    def modify_query(self, query, values: list):
        """Modify the query to retrieve the list of registrations.

        This can be used to apply custom joins etc.
        """
        return query

    def get_filter_criterion(self, values: list):
        """Return an SQLAlchemy filter criterion for the registration list query.

        This is a shorthand for applying a filter via `modify_query` and should be
        preferred for simple cases.
        """

    def filter_list(self, registrations: list[Registration], values: list) -> list[Registration]:
        """Filter the list of registrations after querying it.

        This is intended for cases where an SQL filter is not suitable. Return the new
        list of registrations with any items removed that do not match the filter.
        """
        return registrations

    def load_data(self, registrations: list[Registration]) -> dict[Registration, RegistrationListColumn]:
        """Load the data to show for the displayed registrations.

        This data is then used while iterating over the registrations to display the
        table cells. This method can be omitted in case this item is `filter_only`
        """
        raise NotImplementedError('Custom field is not filter-only but does not provide data')
