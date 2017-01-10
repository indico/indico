# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from indico.core import signals
from indico.util.decorators import classproperty
from indico.util.signals import named_objects_from_signal


class Condition(object):
    """Base class for conditions.

    `Condition`s allow you to define criteria to match on and then evaluate
    those criteria and check whether there is a match (as part of a rule).
    """

    #: The name of the condition. Must be unique within the context
    #: where the condition is used
    name = None
    #: Whether the condition must always be present
    required = False
    #: A short description of the condition.
    description = None
    #: {value: condition_name} containing conditions that are allowed for each value type
    #: non-specified values are considered as compatible with all other conditions.
    compatible_with = None

    @classproperty
    @classmethod
    def friendly_name(cls):
        return cls.name

    @classmethod
    def is_used(cls, rule):
        """Check whether the condition is used in a rule"""
        return rule.get(cls.name) is not None

    @classmethod
    def is_none(cls, **kwargs):
        """Check whether the condition requires a null value.

            Inheriting methods should overload this
        """
        raise NotImplementedError

    @classmethod
    def get_available_values(cls, **kwargs):
        """Get a dict of values that can be used for the condition.

        Subclasses are encouraged to explicitly specify the arguments
        they expect instead of using ``**kwargs``.

        The key of each item is the actual value that will be used
        in the check while the value is what is going to be displayed.

        :param kwargs: arguments specific to the condition's context
        """
        raise NotImplementedError

    @classmethod
    def _clean_values(cls, values, **kwargs):
        return list(cls.get_available_values(**kwargs).viewkeys() & set(values))

    @classmethod
    def check(cls, values, **kwargs):
        """Check whether the condition is matched

        Subclasses are encouraged to explicitly specify the arguments
        they expect instead of using ``**kwargs``.

        This method is only called if the rule is active and if there
        are valid values (as defined by `get_available_values`).

        :param values: a collection of values that are accepted for a
                       match.  it never contains values which are not
                       available anymore.
        :param kwargs: arguments specific to the conditions's context
        """
        raise NotImplementedError


def get_conditions(context, **kwargs):
    """Get a dict of available conditions.

    :param context: the context where the conditions are used
    :param kwargs: arguments specific to the context
    """
    return named_objects_from_signal(signals.get_conditions.send(context, **kwargs))


def check_rule(context, rule, **kwargs):
    """Check whether a rule matches.

    :param context: the context where the conditions are used
    :param rule: the rule to check
    :param kwargs: arguments specific to the context
    """
    for name, condition in get_conditions(context, **kwargs).iteritems():
        if not condition.is_used(rule):
            if condition.required:
                return False
            else:
                continue
        values = condition._clean_values(rule[name], **kwargs)
        if not values and condition.is_none(**kwargs):
            # the property we're checking is null and the rule wants null
            return True
        elif not condition.check(values, **kwargs):
            return False
    return True


def get_missing_conditions(context, rule, **kwargs):
    """Get the set of missing required conditions.

    :param context: the context where the conditions are used
    :param rule: the rule to check
    :param kwargs: arguments specific to the context
    """
    rules = {condition for condition in get_conditions(context, **kwargs).itervalues() if condition.required}
    return {condition.friendly_name for condition in rules if not condition.is_used(rule)}
