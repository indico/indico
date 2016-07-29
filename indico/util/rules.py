# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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


class Rule(object):
    """Base class for rules.

    Rules allow you to define criteria to match on and then evaluate
    those criteria and check whether there is a match.
    """

    #: The name of the rule. Must be unique within the context
    #: where the rule is used
    name = None
    #: Whether the rule must always be present
    required = False
    #: A short description of the rule.
    description = None

    @classproperty
    @classmethod
    def friendly_name(cls):
        return cls.name

    @classmethod
    def is_used(cls, ruleset):
        """Check whether the rule is used in a ruleset"""
        return ruleset.get(cls.name) is not None

    @classmethod
    def get_available_values(cls, **kwargs):
        """Get a dict of values that can be used for the rule.

        Subclasses are encouraged to explicitly specify the arguments
        they expect instead of using ``**kwargs``.

        The key of each item is the actual value that will be used
        in the check while the value is what is going to be displayed.

        :param kwargs: arguments specific to the rule's context
        """
        raise NotImplementedError

    @classmethod
    def _clean_values(cls, values, **kwargs):
        return list(cls.get_available_values(**kwargs).viewkeys() & set(values))

    @classmethod
    def check(cls, values, **kwargs):
        """Check whether the rule is matched

        Subclasses are encouraged to explicitly specify the arguments
        they expect instead of using ``**kwargs``.

        This method is only called if the rule is active and if there
        are valid values (as defined by `get_available_values`).

        :param values: a collection of values that are accepted for a
                       match.  it never contains values which are not
                       available anymore.
        :param kwargs: arguments specific to the rule's context
        """
        raise NotImplementedError


def get_rules(context, **kwargs):
    """Get a dict of available rules.

    :param context: the context where the rules are used
    :param kwargs: arguments specific to the context
    """
    return named_objects_from_signal(signals.get_rules.send(context, **kwargs))


def check_rules(context, ruleset, **kwargs):
    """Check whether a ruleset matches.

    :param context: the context where the rules are used
    :param ruleset: the ruleset to check
    :param kwargs: arguments specific to the context
    """
    for name, rule in get_rules(context, **kwargs).iteritems():
        if not rule.is_used(ruleset):
            if rule.required:
                return False
            else:
                continue
        values = rule._clean_values(ruleset[name], **kwargs)
        # not having empty values is always a failure
        if not values or not rule.check(values, **kwargs):
            return False
    return True


def get_missing_rules(context, ruleset, **kwargs):
    """Get the set of missing required rules.

    :param context: the context where the rules are used
    :param text: the text to check
    :param kwargs: arguments specific to the context
    """
    rules = {rule for rule in get_rules(context, **kwargs).itervalues() if rule.required}
    return {rule.friendly_name for rule in rules if not rule.is_used(ruleset)}
