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

import mimetypes
from collections import defaultdict
from operator import attrgetter

import transaction
from BTrees.IOBTree import IOBTree

from indico.core.db import db
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.modules.events.contributions.models.contributions import Contribution
# from indico.modules.events.paper_reviewing.models.papers import LegacyPaperFile
# from indico.modules.events.paper_reviewing.models.roles import LegacyPaperReviewingRole, PaperReviewingRoleType
from indico.util.console import verbose_iterator
from indico.util.date_time import now_utc
from indico_zodbimport import Importer
from indico_zodbimport.util import LocalFileImporterMixin


def _invert_mapping(mapping):
    result = defaultdict(list)
    for user, contribs in mapping.iteritems():
        for contrib in contribs:
            result[contrib].append(user)
    return result


class LegacyEventPaperReviewingImporter(LocalFileImporterMixin, Importer):
    def __init__(self, **kwargs):
        kwargs = self._set_config_options(**kwargs)
        super(LegacyEventPaperReviewingImporter, self).__init__(**kwargs)

    def migrate(self):
        self.migrate_reviewing()

    def _committing_iterator(self, iterable):
        for i, data in enumerate(iterable, 1):
            yield data
            if i % 100 == 0:
                db.session.commit()
                transaction.commit()
        db.session.commit()
        transaction.commit()

    def _migrate_contribution_roles(self, old_contribution, new_contribution, mapping, role, event_id):
        for avatars in mapping[old_contribution]:
            if not isinstance(avatars, list):
                avatars = [avatars]
            for avatar in avatars:
                new_role = LegacyPaperReviewingRole(user=avatar.user, role=role)
                new_contribution.legacy_paper_reviewing_roles.append(new_role)
                self.print_info('{}: {} -> {}'.format(event_id, new_contribution, new_role))

    def _migrate_resource(self, resource, new_contrib, created_dt, event_id, version=None):

        storage_backend, storage_path, size = self._get_local_file_info(resource)
        content_type = mimetypes.guess_type(resource.fileName)[0] or 'application/octet-stream'

        paper_file = LegacyPaperFile(filename=resource.fileName, created_dt=created_dt,
                                     content_type=content_type, size=size, storage_backend=storage_backend,
                                     storage_file_id=storage_path, contribution=new_contrib,
                                     revision_id=version)

        db.session.add(paper_file)
        self.print_info('{}: {} -> {}'.format(event_id, resource, paper_file))

    def _migrate_reviewing_materials(self, old_contribution, new_contribution, review_manager, event_id):
        reviewing = getattr(old_contribution, 'reviewing', None)
        if reviewing:
            for resource in reviewing._Material__resources.itervalues():
                self._migrate_resource(resource, new_contribution, getattr(reviewing, '_modificationDS', now_utc()),
                                       event_id)
        if review_manager:
            for review in review_manager._versioning:
                if getattr(review, '_materials', None):
                    assert len(review._materials) == 1
                    for resource in review._materials[0]._Material__resources.itervalues():
                        self._migrate_resource(resource, new_contribution, getattr(reviewing, '_modificationDS',
                                                                                   now_utc()),
                                               event_id,
                                               version=review._version)

    def migrate_reviewing(self):
        self.print_step('migrating paper reviewing')
        for conf in self._committing_iterator(self._iter_events()):
            self._migrate_event_reviewing(conf)
            db.session.flush()

    @no_autoflush
    def _migrate_event_reviewing(self, conf):
        conference_settings = getattr(conf, '_confPaperReview', None)
        if not conference_settings:
            return

        event = conf.as_event
        contrib_index = conference_settings._contribution_index = IOBTree()
        contrib_reviewers = _invert_mapping(conference_settings._reviewerContribution)
        contrib_referees = _invert_mapping(conference_settings._refereeContribution)
        contrib_editors = _invert_mapping(conference_settings._editorContribution)

        for old_contribution in conf.contributions.itervalues():
            review_manager = getattr(old_contribution, '_reviewManager', None)
            new_contribution = Contribution.find_one(event_id=event.id, friendly_id=int(old_contribution.id))

            cid = int(new_contribution.id)
            if review_manager:
                review_manager._contrib_id = cid
                contrib_index[cid] = review_manager

            self._migrate_contribution_roles(old_contribution, new_contribution, contrib_reviewers,
                                             PaperReviewingRoleType.reviewer, event.id)
            self._migrate_contribution_roles(old_contribution, new_contribution, contrib_referees,
                                             PaperReviewingRoleType.referee, event.id)
            self._migrate_contribution_roles(old_contribution, new_contribution, contrib_editors,
                                             PaperReviewingRoleType.editor, event.id)

            self._migrate_reviewing_materials(old_contribution, new_contribution, review_manager, event.id)

    def _iter_events(self):
        old_events = self.zodb_root['conferences']
        wfr = self.zodb_root['webfactoryregistry']
        for conf in verbose_iterator(old_events.itervalues(), len(old_events), attrgetter('id'), lambda x: ''):
            if wfr.get(conf.id) is None:
                yield conf
