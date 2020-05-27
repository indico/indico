# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from operator import itemgetter

from flask import flash, redirect, request, session
from sqlalchemy.orm import subqueryload
from werkzeug.exceptions import NotFound

from indico.core.permissions import get_unified_permissions, update_principals_permissions
from indico.modules.events.abstracts import logger
from indico.modules.events.abstracts.controllers.base import RHManageAbstractsBase
from indico.modules.events.abstracts.forms import (AbstractReviewingRolesForm, AbstractReviewingSettingsForm,
                                                   AbstractsScheduleForm, AbstractSubmissionSettingsForm)
from indico.modules.events.abstracts.models.abstracts import Abstract
from indico.modules.events.abstracts.models.review_questions import AbstractReviewQuestion
from indico.modules.events.abstracts.models.review_ratings import AbstractReviewRating
from indico.modules.events.abstracts.models.reviews import AbstractReview
from indico.modules.events.abstracts.operations import close_cfa, open_cfa, schedule_cfa
from indico.modules.events.abstracts.settings import abstracts_reviewing_settings, abstracts_settings
from indico.modules.events.abstracts.views import WPManageAbstracts
from indico.modules.events.operations import (create_reviewing_question, delete_reviewing_question,
                                              sort_reviewing_questions, update_reviewing_question)
from indico.modules.events.reviewing_questions_fields import get_reviewing_field_types
from indico.modules.events.schemas import event_permissions_schema
from indico.modules.events.tracks.models.tracks import Track
from indico.modules.events.tracks.schemas import track_permissions_schema
from indico.modules.events.util import update_object_principals
from indico.util.i18n import _
from indico.util.string import handle_legacy_description
from indico.util.user import principal_from_identifier
from indico.web.flask.util import url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form, jsonify_template


class RHAbstractsDashboard(RHManageAbstractsBase):
    """Dashboard of the abstracts module"""

    # Allow access even if the feature is disabled
    EVENT_FEATURE = None

    def _process(self):
        if not self.event.has_feature('abstracts'):
            return WPManageAbstracts.render_template('management/disabled.html', self.event)
        else:
            abstracts_count = Abstract.query.with_parent(self.event).count()
            return WPManageAbstracts.render_template('management/overview.html', self.event,
                                                     abstracts_count=abstracts_count, cfa=self.event.cfa)


class RHScheduleCFA(RHManageAbstractsBase):
    """Schedule the call for abstracts"""

    def _process(self):
        form = AbstractsScheduleForm(obj=FormDefaults(**abstracts_settings.get_all(self.event)),
                                     event=self.event)
        if form.validate_on_submit():
            rescheduled = self.event.cfa.start_dt is not None
            schedule_cfa(self.event, **form.data)
            if rescheduled:
                flash(_("Call for abstracts has been rescheduled"), 'success')
            else:
                flash(_("Call for abstracts has been scheduled"), 'success')
            return jsonify_data(flash=False)
        return jsonify_form(form)


class RHOpenCFA(RHManageAbstractsBase):
    """Open the call for abstracts"""

    def _process(self):
        open_cfa(self.event)
        flash(_("Call for abstracts is now open"), 'success')
        return redirect(url_for('.management', self.event))


class RHCloseCFA(RHManageAbstractsBase):
    """Close the call for abstracts"""

    def _process(self):
        close_cfa(self.event)
        flash(_("Call for abstracts is now closed"), 'success')
        return redirect(url_for('.management', self.event))


class RHManageAbstractSubmission(RHManageAbstractsBase):
    """Configure abstract submission"""

    def _process(self):
        settings = abstracts_settings.get_all(self.event)
        form = AbstractSubmissionSettingsForm(event=self.event, obj=FormDefaults(**settings))
        if form.validate_on_submit():
            abstracts_settings.set_multi(self.event, form.data)
            flash(_('Abstract submission settings have been saved'), 'success')
            return jsonify_data()
        elif not form.is_submitted():
            handle_legacy_description(form.announcement, settings,
                                      get_render_mode=itemgetter('announcement_render_mode'),
                                      get_value=itemgetter('announcement'))
        return jsonify_form(form)


class RHManageAbstractReviewing(RHManageAbstractsBase):
    """Configure abstract reviewing"""

    def _process(self):
        has_ratings = (AbstractReviewRating.query
                       .join(AbstractReviewRating.review)
                       .join(AbstractReview.abstract)
                       .join(AbstractReviewRating.question)
                       .filter(~Abstract.is_deleted, Abstract.event == self.event,
                               AbstractReviewQuestion.field_type == 'rating')
                       .has_rows())
        defaults = FormDefaults(**abstracts_reviewing_settings.get_all(self.event))
        form = AbstractReviewingSettingsForm(event=self.event, obj=defaults, has_ratings=has_ratings)
        if form.validate_on_submit():
            data = form.data
            abstracts_reviewing_settings.set_multi(self.event, data)
            flash(_('Abstract reviewing settings have been saved'), 'success')
            return jsonify_data()
        self.commit = False
        disabled_fields = form.RATING_FIELDS if has_ratings else ()
        return jsonify_form(form, disabled_fields=disabled_fields)


class RHManageReviewingRoles(RHManageAbstractsBase):
    """Configure track roles (reviewers/conveners)."""

    def _map_event_to_track_permissions(self, permissions):
        filtered_permissions = []
        for (identifier, permission_list) in permissions:
            mapped = []
            if 'convene_all_abstracts' in permission_list:
                mapped.append('convene')
            if 'review_all_abstracts' in permission_list:
                mapped.append('review')
            if mapped:
                filtered_permissions.append((identifier, mapped))
        return filtered_permissions

    def _process(self):
        roles = {}
        event_permissions = event_permissions_schema.dump(self.event).get('acl_entries', {})
        roles['global'] = self._map_event_to_track_permissions(event_permissions)
        tracks = Track.query.with_parent(self.event).options(subqueryload('acl_entries'))
        tracks_by_id = {str(track.id): track for track in tracks}
        for track in tracks:
            roles[str(track.id)] = track_permissions_schema.dump(track).get('acl_entries', {})
        form = AbstractReviewingRolesForm(event=self.event, obj=FormDefaults(roles=roles))

        if form.validate_on_submit():
            role_data = form.data['roles']

            # Update global permissions
            global_conveners = []
            global_reviewers = []
            global_roles = role_data.pop('global')
            for identifier, permissions in global_roles:
                principal = principal_from_identifier(identifier, allow_groups=True, allow_event_roles=True,
                                                      allow_category_roles=True, event_id=self.event.id)
                if 'convene' in permissions:
                    global_conveners.append(principal)
                if 'review' in permissions:
                    global_reviewers.append(principal)
            update_object_principals(self.event, global_conveners, permission='convene_all_abstracts')
            update_object_principals(self.event, global_reviewers, permission='review_all_abstracts')

            # Update track specific permissions
            track_conveners = []
            track_reviewers = []
            for (track_id, track_roles) in role_data.items():
                acl_entries = {}
                for identifier, permissions in track_roles:
                    principal = principal_from_identifier(identifier, allow_groups=True, allow_event_roles=True,
                                                          allow_category_roles=True, event_id=self.event.id)
                    acl_entries[principal] = set(permissions)
                    if 'convene' in permissions:
                        track_conveners.append(principal)
                    if 'review' in permissions:
                        track_reviewers.append(principal)
                track = tracks_by_id[track_id]
                current = {e.principal: get_unified_permissions(e) for e in track.acl_entries}
                update_principals_permissions(track, current, acl_entries)

            # Update event ACL for track and global permissions
            all_conveners = set(global_conveners + track_conveners)
            all_reviewers = set(global_reviewers + track_reviewers)
            update_object_principals(self.event, all_conveners, permission='track_convener')
            update_object_principals(self.event, all_reviewers, permission='abstract_reviewer')

            flash(_("Abstract reviewing roles have been updated."), 'success')
            logger.info("Abstract reviewing roles of %s have been updated by %s", self.event, session.user)
            return jsonify_data()
        return jsonify_form(form, skip_labels=True, form_header_kwargs={'id': 'reviewing-role-form'},
                            disabled_until_change=False)


class RHManageAbstractReviewingQuestions(RHManageAbstractsBase):
    def _process(self):
        endpoints = {'create': 'abstracts.create_reviewing_question', 'edit': 'abstracts.edit_reviewing_question',
                     'delete': 'abstracts.delete_reviewing_question', 'sort': 'abstracts.sort_reviewing_questions'}
        return jsonify_template('events/reviewing_questions_management.html', event=self.event,
                                reviewing_questions=self.event.abstract_review_questions,
                                field_types=get_reviewing_field_types('abstracts'), endpoints=endpoints,
                                common_url_args={})


class RHCreateAbstractReviewingQuestion(RHManageAbstractsBase):
    def _process_args(self):
        RHManageAbstractsBase._process_args(self)
        try:
            self.field_cls = get_reviewing_field_types('abstracts')[request.args['field_type']]
        except KeyError:
            raise NotFound

    def _process(self):
        form = self.field_cls.create_config_form()
        if form.validate_on_submit():
            new_question = create_reviewing_question(self.event, AbstractReviewQuestion, self.field_cls, form)
            self.event.abstract_review_questions.append(new_question)
            logger.info("Abstract reviewing question %r created by %r", new_question, session.user)
            return jsonify_data(flash=False)
        return jsonify_form(form, fields=getattr(form, '_order', None))


class RHReviewingQuestionBase(RHManageAbstractsBase):
    locator_args = {
        lambda self: self.question
    }

    def _process_args(self):
        RHManageAbstractsBase._process_args(self)
        self.question = AbstractReviewQuestion.get_or_404(request.view_args['question_id'])


class RHEditAbstractReviewingQuestion(RHReviewingQuestionBase):
    def _process(self):
        defaults = FormDefaults(obj=self.question, **self.question.field_data)
        form = self.question.field.create_config_form(obj=defaults)
        if form.validate_on_submit():
            update_reviewing_question(self.question, form)
            return jsonify_data(flash=False)
        return jsonify_form(form, fields=getattr(form, '_order', None))


class RHDeleteAbstractReviewingQuestion(RHReviewingQuestionBase):
    def _process(self):
        delete_reviewing_question(self.question)
        return jsonify_data(flash=False)


class RHSortReviewingQuestions(RHManageAbstractsBase):
    def _process(self):
        question_ids = map(int, request.form.getlist('field_ids'))
        sort_reviewing_questions(self.event.abstract_review_questions, question_ids)
        return jsonify_data(flash=False)
