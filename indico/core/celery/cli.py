# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import click
from celery.bin.celery import celery as celery_cmd

from indico.core.celery.util import unlock_task
from indico.util.console import cformat


# remove the celery shell command
del celery_cmd.commands['shell']


@celery_cmd.command()
@click.argument('name')
def unlock(name):
    """Unlock a locked task.

    Use this if your celery worker was e.g. killed by your kernel's
    oom-killer and thus a task never got unlocked.

    Examples:

        indico celery unlock event_reminders
    """

    if unlock_task(name):
        print(cformat('%{green!}Task {} unlocked').format(name))
    else:
        print(cformat('%{yellow}Task {} is not locked').format(name))
