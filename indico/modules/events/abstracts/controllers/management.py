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

from collections import defaultdict
from operator import attrgetter

from flask import redirect, flash, jsonify, request, session
from sqlalchemy.orm import joinedload, subqueryload
from werkzeug.exceptions import Forbidden

from indico.modules.events.abstracts import logger
from indico.modules.events.abstracts.controllers.base import (AbstractMixin, DisplayAbstractListMixin,
                                                              CustomizeAbstractListMixin, AbstractsExportPDFMixin,
                                                              AbstractsDownloadAttachmentsMixin, AbstractsExportCSV,
                                                              AbstractsExportExcel, AbstractPageMixin)
from indico.modules.events.abstracts.forms import (AbstractSubmissionSettingsForm,
                                                   AbstractReviewingRolesForm, AbstractReviewingSettingsForm,
                                                   AbstractsScheduleForm, BulkAbstractJudgmentForm)
from indico.modules.events.abstracts.models.abstracts import Abstract, AbstractState
from indico.modules.events.abstracts.models.persons import AbstractPersonLink
from indico.modules.events.abstracts.models.review_ratings import AbstractReviewRating
from indico.modules.events.abstracts.models.reviews import AbstractReview
from indico.modules.events.abstracts.operations import (create_abstract, delete_abstract, schedule_cfa, open_cfa,
                                                        close_cfa, judge_abstract, update_abstract)
from indico.modules.events.abstracts.schemas import abstracts_schema
from indico.modules.events.abstracts.settings import abstracts_settings, abstracts_reviewing_settings
from indico.modules.events.abstracts.util import (make_abstract_form, get_roles_for_event,
                                                  AbstractListGeneratorManagement)
from indico.modules.events.abstracts.views import WPManageAbstracts
from indico.modules.events.contributions.models.persons import AuthorType
from indico.modules.events.util import get_field_values, update_object_principals
from indico.util.fs import secure_filename
from indico.util.i18n import _, ngettext
from indico.web.flask.util import send_file, url_for
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form, jsonify_template
from MaKaC.PDFinterface.conference import ConfManagerAbstractToPDF
from MaKaC.webinterface.rh.base import RH
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHManageAbstractsBase(RHConferenceModifBase):
    """Base class for all abstracts management RHs"""

    CSRF_ENABLED = True
    EVENT_FEATURE = 'abstracts'

    def _process(self):
        return RH._process(self)


class RHManageAbstractBase(AbstractMixin, RHManageAbstractsBase):
    """Base class for all abstract management RHs"""

    def _checkParams(self, params):
        RHManageAbstractsBase._checkParams(self, params)
        AbstractMixin._checkParams(self)

    def _checkProtection(self):
        RHManageAbstractsBase._checkProtection(self)
        AbstractMixin._checkProtection(self)


class RHAbstractListBase(RHManageAbstractsBase):
    """Base class for all abstract list operations"""

    def _checkParams(self, params):
        RHManageAbstractsBase._checkParams(self, params)
        self.list_generator = AbstractListGeneratorManagement(event=self.event_new)


class RHManageAbstractsActionsBase(RHAbstractListBase):
    """Base class for classes performing actions on abstract"""

    _abstract_query_options = ()

    @property
    def _abstract_query(self):
        query = Abstract.query.with_parent(self.event_new)
        if self._abstract_query_options:
            query = query.options(*self._abstract_query_options)
        return query

    def _checkParams(self, params):
        RHAbstractListBase._checkParams(self, params)
        ids = map(int, request.form.getlist('abstract_id'))
        self.abstracts = self._abstract_query.filter(Abstract.id.in_(ids)).all()


class RHManageAbstract(AbstractPageMixin, RHConferenceModifBase):
    """Display abstract management page"""

    CSRF_ENABLED = True
    management = True
    page_class = WPManageAbstracts

    def _checkProtection(self):
        RHConferenceModifBase._checkProtection(self)
        AbstractPageMixin._checkProtection(self)

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        AbstractPageMixin._checkParams(self)


class RHBulkAbstractJudgment(RHManageAbstractsActionsBase):
    """Perform bulk judgment operations on selected abstracts"""

    def _process(self):
        form = BulkAbstractJudgmentForm(event=self.event_new, abstract_id=[a.id for a in self.abstracts],
                                        judgment=request.form.get('judgment'))
        if form.process_ajax():
            return form.ajax_response
        elif form.validate_on_submit():
            judgment_data, abstract_data = form.split_data
            submitted_abstracts = {abstract for abstract in self.abstracts if abstract.state == AbstractState.submitted}
            for abstract in submitted_abstracts:
                judge_abstract(abstract, abstract_data, judge=session.user, **judgment_data)
            num_judged_abstracts = len(submitted_abstracts)
            num_prejudged_abstracts = len(self.abstracts) - num_judged_abstracts
            if num_judged_abstracts:
                flash(ngettext("One abstract has been judged.",
                               "{num} abstracts have been judged.",
                               num_judged_abstracts).format(num=num_judged_abstracts), 'success')
            if num_prejudged_abstracts:
                flash(ngettext("One abstract has been skipped since it is already judged.",
                               "{num} abstracts have been skipped since they are already judged.",
                               num_prejudged_abstracts).format(num=num_prejudged_abstracts), 'warning')
            return jsonify_data(**self.list_generator.render_list())
        return jsonify_form(form=form, submit=_('Judge'), disabled_until_change=False)


class RHAbstractNotificationLog(RHManageAbstractBase):

    def _checkProtection(self):
        RHManageAbstractBase._checkProtection(self)
        if not self.abstract.can_judge(session.user, check_state=False):
            raise Forbidden

    def _process(self):
        return WPManageAbstracts.render_template('abstract/notification_log.html', self._conf, abstract=self.abstract)


class RHEditAbstract(RHManageAbstractBase):
    def _process(self):
        abstract_form_class = make_abstract_form(self.event_new)
        form = abstract_form_class(obj=self.abstract, abstract=self.abstract, event=self.event_new)
        # TODO Handle reviewed_for_tracks properly
        if form.validate_on_submit():
            data = form.data
            if isinstance(data['submitted_for_tracks'], Track):
                data['submitted_for_tracks'] = {data['submitted_for_tracks']}
            elif data['submitted_for_tracks'] is None:
                data['submitted_for_tracks'] = set()
            update_abstract(self.abstract, *get_field_values(data))
            flash(_("Abstract modified successfully"), 'success')
            return jsonify_data(flash=False)
        self.commit = False
        return jsonify_form(form)


class RHAbstractExportPDF(RHManageAbstractBase):
    def _process(self):
        pdf = ConfManagerAbstractToPDF(self.abstract)
        file_name = secure_filename('abstract-{}.pdf'.format(self.abstract.friendly_id), 'abstract.pdf')
        return send_file(file_name, pdf.generate(), 'application/pdf')


class RHAbstracts(RHManageAbstractsBase):
    """Display abstracts management page"""

    EVENT_FEATURE = None

    def _process(self):
        if not self.event_new.has_feature('abstracts'):
            return WPManageAbstracts.render_template('management/disabled.html', self._conf, event=self.event_new)
        else:
            abstracts_count = Abstract.query.with_parent(self.event_new).count()
            return WPManageAbstracts.render_template('management/overview.html', self._conf, event=self.event_new,
                                                     abstracts_count=abstracts_count, cfa=self.event_new.cfa)


class RHScheduleCFA(RHManageAbstractsBase):
    """Schedule the call for abstracts"""

    def _process(self):
        form = AbstractsScheduleForm(obj=FormDefaults(**abstracts_settings.get_all(self.event_new)),
                                     event=self.event_new)
        if form.validate_on_submit():
            rescheduled = self.event_new.cfa.start_dt is not None
            schedule_cfa(self.event_new, **form.data)
            if rescheduled:
                flash(_("Call for abstracts has been rescheduled"), 'success')
            else:
                flash(_("Call for abstracts has been scheduled"), 'success')
            return jsonify_data(flash=False)
        return jsonify_form(form)


class RHOpenCFA(RHManageAbstractsBase):
    """Opens the call for abstracts"""

    def _process(self):
        open_cfa(self.event_new)
        flash(_("Call for abstracts is now open"), 'success')
        return redirect(url_for('.manage_abstracts', self.event_new))


class RHCloseCFA(RHManageAbstractsBase):
    """Closes the call for abstracts"""

    def _process(self):
        close_cfa(self.event_new)
        flash(_("Call for abstracts is now closed"), 'success')
        return redirect(url_for('.manage_abstracts', self.event_new))


class RHManageAbstractSubmission(RHManageAbstractsBase):
    """Configure abstract submission"""

    def _process(self):
        form = AbstractSubmissionSettingsForm(event=self.event_new,
                                              obj=FormDefaults(**abstracts_settings.get_all(self.event_new)))
        if form.validate_on_submit():
            abstracts_settings.set_multi(self.event_new, form.data)
            flash(_('Abstract submission settings have been saved'), 'success')
            return jsonify_data()
        return jsonify_form(form)


class RHManageAbstractReviewing(RHManageAbstractsBase):
    """Configure abstract reviewing"""

    def _process(self):
        has_ratings = bool(AbstractReviewRating.query
                           .join(AbstractReviewRating.review)
                           .join(AbstractReview.abstract)
                           .filter(~Abstract.is_deleted, Abstract.event_new == self.event_new)
                           .count())
        defaults = FormDefaults(abstract_review_questions=self.event_new.abstract_review_questions,
                                **abstracts_reviewing_settings.get_all(self.event_new))
        form = AbstractReviewingSettingsForm(event=self.event_new, obj=defaults, has_ratings=has_ratings)
        if form.validate_on_submit():
            data = form.data
            # XXX: we need to do this assignment for new questions,
            # but editing or deleting existing questions changes an
            # object that is already in the session so it's updated
            # in any case
            self.event_new.abstract_review_questions = data.pop('abstract_review_questions')
            abstracts_reviewing_settings.set_multi(self.event_new, data)
            flash(_('Abstract reviewing settings have been saved'), 'success')
            return jsonify_data()
        self.commit = False
        disabled_fields = form.RATING_FIELDS if has_ratings else ()
        return jsonify_form(form, disabled_fields=disabled_fields)


class RHAbstractList(DisplayAbstractListMixin, RHAbstractListBase):
    template = 'management/abstract_list.html'
    view_class = WPManageAbstracts


class RHAbstractListCustomize(CustomizeAbstractListMixin, RHAbstractListBase):
    view_class = WPManageAbstracts


class RHAbstractListStaticURL(RHAbstractListBase):
    """Generate a static URL for the configuration of the abstract list"""

    def _process(self):
        return jsonify(url=self.list_generator.generate_static_url())


class RHCreateAbstract(RHAbstractListBase):
    def _process(self):
        abstract_form_class = make_abstract_form(self.event_new)
        form = abstract_form_class(event=self.event_new)
        if form.validate_on_submit():
            data = form.data
            abstract = create_abstract(self.event_new, *get_field_values(data))
            flash(_("Abstract '{}' created successfully").format(abstract.title), 'success')
            tpl_components = self.list_generator.render_list(abstract)
            if tpl_components.get('hide_abstract'):
                self.list_generator.flash_info_message(abstract)
            return jsonify_data(**tpl_components)
        return jsonify_template('events/abstracts/forms/abstract.html', event=self.event_new, form=form)


class RHDeleteAbstracts(RHManageAbstractsActionsBase):
    def _process(self):
        delete_contribs = request.values.get('delete_contribs') == '1'
        deleted_contrib_count = 0
        for abstract in self.abstracts:
            if delete_contribs and abstract.contribution:
                deleted_contrib_count += 1
            delete_abstract(abstract, delete_contribs)
        deleted_abstract_count = len(self.abstracts)
        flash(ngettext("The abstract has been deleted.",
                       "{count} abstracts have been deleted.", deleted_abstract_count)
              .format(count=deleted_abstract_count), 'success')
        if deleted_contrib_count:
            flash(ngettext("The linked contribution has been deleted.",
                           "{count} linked contributions have been deleted.", deleted_contrib_count)
                  .format(count=deleted_contrib_count), 'success')
        return jsonify_data(**self.list_generator.render_list())


class RHAbstractPersonList(RHManageAbstractsActionsBase):
    """List of persons somehow related to abstracts (co-authors, speakers...)"""

    @property
    def _membership_filter(self):
        abstract_ids = {abstract.id for abstract in self.abstracts}
        return Abstract.id.in_(abstract_ids)

    def _process(self):
        submitters = {abstract.submitter for abstract in self.abstracts}
        abstract_persons = AbstractPersonLink.find_all(AbstractPersonLink.abstract.has(self._membership_filter))
        abstract_persons_dict = defaultdict(lambda: {'speaker': False, 'submitter': False, 'primary_author': False,
                                                     'secondary_author': False})
        for abstract_person in abstract_persons:
            dict_key = abstract_person.person.user if abstract_person.person.user else abstract_person.person
            person_roles = abstract_persons_dict[dict_key]
            person_roles['speaker'] |= abstract_person.is_speaker
            person_roles['primary_author'] |= abstract_person.author_type == AuthorType.primary
            person_roles['secondary_author'] |= abstract_person.author_type == AuthorType.secondary
        for submitter in submitters:
            abstract_persons_dict[submitter]['submitter'] |= True
        return jsonify_template('events/management/contribution_person_list.html',
                                event_persons=abstract_persons_dict, event=self.event_new, include_submitters=True)


class RHAbstractsDownloadAttachments(AbstractsDownloadAttachmentsMixin, RHManageAbstractsActionsBase):
    pass


class RHAbstractsExportPDF(AbstractsExportPDFMixin, RHManageAbstractsActionsBase):
    pass


class RHAbstractsExportCSV(AbstractsExportCSV, RHManageAbstractsActionsBase):
    pass


class RHAbstractsExportExcel(AbstractsExportExcel, RHManageAbstractsActionsBase):
    pass


class RHAbstractsExportJSON(RHManageAbstractsActionsBase):
    _abstract_query_options = (joinedload('submitter'),
                               joinedload('accepted_track'),
                               joinedload('accepted_contrib_type'),
                               joinedload('submitted_contrib_type'),
                               subqueryload('field_values'),
                               subqueryload('submitted_for_tracks'),
                               subqueryload('reviewed_for_tracks'),
                               subqueryload('person_links'),
                               subqueryload('reviews').joinedload('ratings'))

    def _process(self):
        sorted_abstracts = sorted(self.abstracts, key=attrgetter('friendly_id'))
        response = jsonify(version=1, abstracts=abstracts_schema.dump(sorted_abstracts).data)
        response.headers['Content-Disposition'] = 'attachment; filename="abstracts.json"'
        return response


class RHManageReviewingRoles(RHManageAbstractsBase):
    """Configure track roles (reviewers/conveners)."""

    def _process(self):
        roles = get_roles_for_event(self.event_new)
        form = AbstractReviewingRolesForm(event=self.event_new, obj=FormDefaults(roles=roles))

        if form.validate_on_submit():
            role_data = form.roles.role_data
            self.event_new.global_conveners = set(role_data['global_conveners'])
            self.event_new.global_abstract_reviewers = set(role_data['global_reviewers'])

            for track, user_roles in role_data['track_roles'].viewitems():
                track.conveners = set(user_roles['convener'])
                track.abstract_reviewers = set(user_roles['reviewer'])

            # Update actual ACLs
            update_object_principals(self.event_new, role_data['all_conveners'], role='track_convener')
            update_object_principals(self.event_new, role_data['all_reviewers'], role='abstract_reviewer')

            flash(_("Abstract reviewing roles have been updated."), 'success')
            logger.info("Abstract reviewing roles of %s have been updated by %s", self.event_new, session.user)
            return jsonify_data()
        return jsonify_form(form, skip_labels=True, form_header_kwargs={'id': 'reviewing-role-form'},
                            disabled_until_change=True)
