# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

# This script lets you undo a merge, provided you have an Indico server
# which still contains the unmerged data (as recent as possible).
# It collects the correct associations on that server and gives you
# a blob of data which you can then load on the production server.

# Please note that this script only restores certain linked objects.
# You **MUST** check which links the user actually has and add code for the missing ones!
# To perform the check, you can run this script's `show_links` command.

from __future__ import unicode_literals

import json
import sys
from operator import methodcaller

import click
import transaction

from indico.core.db import DBMgr
from indico.util.redis import avatar_links, suggestions
from MaKaC.common.indexes import IndexesHolder
from MaKaC.common.ObjectHolders import ObjectHolder
from MaKaC.conference import ConferenceHolder
from MaKaC.user import AvatarHolder


def _valid_event(event_or_id):
    if event_or_id is None:
        return False
    event_id = event_or_id.getId() if hasattr(event_or_id, 'getId') else event_or_id
    return ConferenceHolder().getById(event_id, quiet=True) is not None


# TODO: Add extra items here as necessary (use show_links to check if anything is missing)!
retrieve_link_map = {
    ('conference', 'access'): (methodcaller('getId'), _valid_event),
    ('contribution', 'submission'): (lambda contrib: (contrib.getConference().getId(), contrib.getId()),
                                     lambda contrib: _valid_event(contrib.getConference())),
    ('contribution', 'manager'): (lambda contrib: (contrib.getConference().getId(), contrib.getId()),
                                  lambda contrib: _valid_event(contrib.getConference())),
}


# noinspection PyUnusedLocal
def validate_avatars(ctx, param, value):
    avatars = tuple(AvatarHolder().getById(x) for x in value)
    for i, avatar in enumerate(avatars):
        if not avatar:
            raise click.BadParameter("no such avatar: {}".format(value[i]))
    if avatars[0] == avatars[1]:
        raise click.BadParameter("you need to specify two different avatars")
    return avatars


def echo(message=''):
    click.echo(message, file=sys.stderr)


@click.group()
def main():
    pass


@main.command()
@click.argument('avatars', nargs=2, required=True, callback=validate_avatars)
def show_links(avatars):
    """Step 0: Show the used links"""
    used_links = set()
    for avatar in avatars:
        for objtype, linkdict in avatar.linkedTo.iteritems():
            for role, links in linkdict.iteritems():
                if set(links):
                    used_links.add((objtype, role))
    echo('The following links are used by the specified avatars:')
    for objtype, role in used_links:
        echo('  - {}.{}'.format(objtype, role))

    echo()
    if all(entry in retrieve_link_map for entry in used_links):
        echo('You are lucky; all used links are already implemented')
    else:
        echo('The following links are not implemented yet:')
        for entry in used_links:
            if entry not in retrieve_link_map:
                echo('  - {}.{}'.format(*entry))


@main.command()
@click.option('-f', '--file', type=click.File('w'), default='-')
@click.argument('avatars', nargs=2, required=True, callback=validate_avatars)
def retrieve_associations(file, avatars):
    """Step 1: Retrieves the associations

    Run this on a PRE-MERGE database.
    The association information is written to the specified file or stdout.
    """
    data = []
    for avatar in avatars:
        avatar_data = {'id': avatar.getId(),
                       'links': {},
                       'secondary_emails': avatar.getSecondaryEmails()}
        for (objtype, role), (accessor, condition) in retrieve_link_map.iteritems():
            avatar_data['links']['{}.{}'.format(objtype, role)] = [accessor(link)
                                                                   for link in avatar.linkedTo[objtype][role]
                                                                   if condition is None or condition(link)]
        if avatar.api_key is not None:
            echo('Avatar {} has an API key; API key splitting is not implemented yet!'.format(avatar))
        # TODO: check room booking
        data.append(avatar_data)
    json.dump(data, file)
    echo("Data export successful")


@main.command()
@click.argument('file', type=click.File(), default='-')
def split_avatars(file):
    """Step 2: Split the merged avatars - run this on the POST-MERGE database"""
    data = json.load(file)
    if len(data) != 2:
        echo('Invalid data: Expected two items, found {}'.format(len(data)))
        raise click.Abort()
    avatars = [AvatarHolder().getById(x['id']) for x in data]
    if avatars.count(None) != 1:
        echo('Expected exactly one unreferenced avatar, got {}'.format(avatars))
        raise click.Abort()
    if avatars[0] is None:
        orig = avatars[1]
        orig_data = data[1]
        merged_data = data[0]
    else:
        orig = avatars[0]
        orig_data = data[0]
        merged_data = data[1]
    merged = [av for av in orig._mergeFrom if av.getId() == merged_data['id']]
    if len(merged) != 1:
        echo("Avatars don't seem to be merged into each other")
        raise click.Abort()
    merged = merged[0]
    if merged not in orig._mergeFrom or merged._mergeTo != orig:
        echo("Avatars don't seem to be merged into each other")
        raise click.Abort()
    # Remove merge references
    orig._mergeFrom.remove(merged)
    merged._mergeTo = None
    # Clean secondary emails
    orig.setSecondaryEmails(orig_data['secondary_emails'])
    merged.setSecondaryEmails(merged_data['secondary_emails'])
    # Clean identities
    for identity in merged.getIdentityList(create_identities=True):
        orig.removeIdentity(identity)
        identity.setUser(merged)
    # Re-index the avatars
    # noinspection PyCallByClass
    ObjectHolder.add(AvatarHolder(), merged)
    for index in {'organisation', 'email', 'name', 'surName', 'status'}:
        IndexesHolder().getById(index).unindexUser(orig)
        IndexesHolder().getById(index).indexUser(orig)
        IndexesHolder().getById(index).indexUser(merged)
    # Restore links for the merged avatar
    for key, links in merged_data['links'].iteritems():
        objtype, role = key.split('.')
        for link in links:
            # TODO: Add extra items here as necessary (use show_links to check if anything is missing)!
            if objtype == 'conference':
                event = ConferenceHolder().getById(link, quiet=True)
                if event is None:
                    echo('Event not found: {}'.format(link))
                    continue
                if event not in set(orig.linkedTo[objtype][role]):
                    echo('{!r} not linked to avatar via {}'.format(event, key))
                    continue
                if role == 'access':
                    event.revokeAccess(orig)
                    event.grantAccess(merged)
                else:
                    echo('Unexpected link type: {}'.format(key))
                    raise click.Abort()
                # print 'Updated {} - {!r}'.format(key, event)
            elif objtype == 'contribution':
                event_id, contrib_id = link
                event = ConferenceHolder().getById(event_id)
                if event is None:
                    echo('Event not found: {}'.format(event_id))
                    continue
                contrib = event.getContributionById(contrib_id)
                if contrib is None:
                    echo('Contrib not found: {}.{}'.format(event_id, contrib_id))
                    continue
                if contrib not in set(orig.linkedTo[objtype][role]):
                    echo('{} not linked to avatar via {}'.format(contrib, key))
                    continue
                if role == 'submission':
                    contrib.revokeSubmission(orig)
                    contrib.grantSubmission(merged)
                elif role == 'manager':
                    contrib.revokeModification(orig)
                    contrib.grantModification(merged)
                else:
                    echo('Unexpected link type: {}'.format(key))
                    raise click.Abort()
                # print 'Updated {} - {}'.format(key, contrib)
            else:
                # This results in inconsistent data in redis, but since we flush the redis
                # links after a successful merge, that's not an issue. Also, we only reach
                # this branch if someone is using different versions of this script...
                echo('Unexpected link type: {}'.format(key))
                raise click.Abort()
    if not click.confirm('Do you want to commit the changes now?'):
        transaction.abort()  # not really necessary, but let's stay on the safe side
        raise click.Abort()
    transaction.commit()
    # Refresh redis links
    avatar_links.delete_avatar(orig)
    avatar_links.delete_avatar(merged)
    avatar_links.init_links(orig)
    avatar_links.init_links(merged)
    # Delete suggestions
    suggestions.delete_avatar(orig)
    suggestions.delete_avatar(merged)


if __name__ == '__main__':
    with DBMgr.getInstance().global_connection():
        main()
