# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import click

from indico.cli.core import cli_group
from indico.core.db import db
from indico.core.db.sqlalchemy.principals import PrincipalType
from indico.core.db.sqlalchemy.util.models import get_simple_column_attrs
from indico.modules.attachments import Attachment, AttachmentFolder
from indico.modules.attachments.models.principals import AttachmentFolderPrincipal, AttachmentPrincipal
from indico.modules.events.contributions import Contribution
from indico.modules.events.contributions.models.principals import ContributionPrincipal
from indico.modules.events.models.principals import EventPrincipal
from indico.modules.events.models.roles import EventRole
from indico.modules.events.sessions import Session
from indico.modules.events.sessions.models.principals import SessionPrincipal


click.disable_unicode_literals_warning = True


@cli_group()
def cli():
    pass


def _fix_role_principals(principals, get_event):
    role_attrs = get_simple_column_attrs(EventRole) | {'members'}
    for p in principals:
        click.echo('Fixing {}'.format(p))
        event = get_event(p)
        try:
            event_role = [r for r in event.roles if r.code == p.event_role.code][0]
        except IndexError:
            event_role = EventRole(event=event)
            event_role.populate_from_attrs(p.event_role, role_attrs)
        else:
            click.echo('  using existing role {}'.format(event_role))
        p.event_role = event_role
    db.session.flush()


@cli.command()
def fix_event_role_acls():
    """Fix ACLs referencing event roles from other events.

    This happened due to a bug prior to 2.2.3 when cloning an event
    which had event roles in its ACL.
    """
    fixed_something = False
    broken = (EventPrincipal.query
              .join(EventRole, EventRole.id == EventPrincipal.event_role_id)
              .filter(EventPrincipal.type == PrincipalType.event_role, EventPrincipal.event_id != EventRole.event_id)
              .all())
    _fix_role_principals(broken, lambda p: p.event)
    fixed_something = fixed_something or bool(broken)

    broken = (SessionPrincipal.query
              .join(Session, Session.id == SessionPrincipal.session_id)
              .join(EventRole, EventRole.id == SessionPrincipal.event_role_id)
              .filter(SessionPrincipal.type == PrincipalType.event_role, Session.event_id != EventRole.event_id)
              .all())
    _fix_role_principals(broken, lambda p: p.session.event)
    fixed_something = fixed_something or bool(broken)

    broken = (ContributionPrincipal.query
              .join(Contribution, Contribution.id == ContributionPrincipal.contribution_id)
              .join(EventRole, EventRole.id == ContributionPrincipal.event_role_id)
              .filter(ContributionPrincipal.type == PrincipalType.event_role,
                      Contribution.event_id != EventRole.event_id)
              .all())
    _fix_role_principals(broken, lambda p: p.contribution.event)
    fixed_something = fixed_something or bool(broken)

    broken = (AttachmentFolderPrincipal.query
              .join(AttachmentFolder, AttachmentFolder.id == AttachmentFolderPrincipal.folder_id)
              .join(EventRole, EventRole.id == AttachmentFolderPrincipal.event_role_id)
              .filter(AttachmentFolderPrincipal.type == PrincipalType.event_role,
                      AttachmentFolder.event_id != EventRole.event_id)
              .all())
    _fix_role_principals(broken, lambda p: p.folder.event)
    fixed_something = fixed_something or bool(broken)

    broken = (AttachmentPrincipal.query
              .join(Attachment, Attachment.id == AttachmentPrincipal.attachment_id)
              .join(AttachmentFolder, AttachmentFolder.id == Attachment.folder_id)
              .join(EventRole, EventRole.id == AttachmentPrincipal.event_role_id)
              .filter(AttachmentPrincipal.type == PrincipalType.event_role,
                      AttachmentFolder.event_id != EventRole.event_id)
              .all())
    _fix_role_principals(broken, lambda p: p.attachment.folder.event)
    fixed_something = fixed_something or bool(broken)

    if not fixed_something:
        click.secho('Nothing to fix :)', fg='green')
        return

    click.confirm(click.style('Do you want to commit the fixes shown above?', fg='white', bold=True),
                  default=True, abort=True)
    db.session.commit()
    click.secho('Success!', fg='green')
