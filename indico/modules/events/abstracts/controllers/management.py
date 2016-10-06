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

import os
from collections import defaultdict
from operator import attrgetter

from flask import redirect, flash, jsonify, request

from indico.core.db import db
from indico.modules.events.abstracts.controllers.base import AbstractMixin
from indico.modules.events.abstracts.forms import (BOASettingsForm, AbstractSubmissionSettingsForm,
                                                   AbstractReviewingSettingsForm)
from indico.modules.events.abstracts.models.abstracts import Abstract
from indico.modules.events.abstracts.models.persons import AbstractPersonLink
from indico.modules.events.abstracts.models.review_ratings import AbstractReviewRating
from indico.modules.events.abstracts.models.reviews import AbstractReview
from indico.modules.events.abstracts.operations import create_abstract, delete_abstract
from indico.modules.events.abstracts.settings import boa_settings, abstracts_settings, abstracts_reviewing_settings
from indico.modules.events.abstracts.util import AbstractListGenerator, make_abstract_form
from indico.modules.events.abstracts.views import WPManageAbstracts
from indico.modules.events.contributions.models.persons import AuthorType
from indico.modules.events.tracks.models.tracks import Track
from indico.modules.events.util import get_field_values, ZipGeneratorMixin
from indico.util.fs import secure_filename
from indico.util.i18n import _, ngettext
from indico.web.flask.util import send_file
from indico.web.forms.base import FormDefaults
from indico.web.util import jsonify_data, jsonify_form, jsonify_template
from MaKaC.PDFinterface.conference import ConfManagerAbstractsToPDF
from MaKaC.webinterface.rh.base import RH
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHManageAbstractsBase(RHConferenceModifBase):
    """Base class for all abstracts management RHs"""

    CSRF_ENABLED = True
    EVENT_FEATURE = 'abstracts'

    def _process(self):
        return RH._process(self)


class RHAbstractListBase(RHManageAbstractsBase):
    """Base class for all abstract list operations"""

    def _checkParams(self, params):
        RHManageAbstractsBase._checkParams(self, params)
        self.list_generator = AbstractListGenerator(event=self.event_new)


class RHManageAbstractsActionsBase(RHAbstractListBase):
    """Base class for classes performing actions on abstract"""

    def _checkParams(self, params):
        RHAbstractListBase._checkParams(self, params)
        ids = map(int, request.form.getlist('abstract_id'))
        self.abstracts = Abstract.query.with_parent(self.event_new).filter(Abstract.id.in_(ids)).all()


class RHManageAbstract(AbstractMixin, RHManageAbstractsBase):
    def _checkParams(self, params):
        RHManageAbstractsBase._checkParams(self, params)
        AbstractMixin._checkParams(self)

    def _checkProtection(self):
        RHManageAbstractsBase._checkProtection(self)
        AbstractMixin._checkProtection(self)

    def _process(self):
        return WPManageAbstracts.render_template('management/abstract.html', self._conf, abstract=self.abstract)


class RHAbstracts(RHManageAbstractsBase):
    """Display abstracts management page"""

    def _process(self):
        abstracts_count = Abstract.query.with_parent(self.event_new).count()
        return WPManageAbstracts.render_template('management/abstracts.html', self._conf, event=self.event_new,
                                                 abstracts_count=abstracts_count)


class RHManageBOA(RHManageAbstractsBase):
    """Configure book of abstracts"""

    def _process(self):
        form = BOASettingsForm(obj=FormDefaults(**boa_settings.get_all(self.event_new)))
        if form.validate_on_submit():
            boa_settings.set_multi(self.event_new, form.data)
            flash(_('Book of Abstract settings have been saved'), 'success')
            return jsonify_data()
        return jsonify_form(form)


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


class RHAbstractList(RHAbstractListBase):
    """Display the list of abstracts"""

    def _process(self):
        if self.list_generator.static_link_used:
            return redirect(self.list_generator.get_list_url())
        list_kwargs = self.list_generator.get_list_kwargs()
        return WPManageAbstracts.render_template('management/abstract_list.html', self._conf, event=self.event_new,
                                                 **list_kwargs)


class RHAbstractListCustomize(RHAbstractListBase):
    """Filter options and columns to display for the abstract list of an event"""

    def _process_GET(self):
        list_config = self.list_generator._get_config()
        return WPManageAbstracts.render_template('management/abstract_list_filter.html', self._conf,
                                                 event=self.event_new, visible_items=list_config['items'],
                                                 static_items=self.list_generator.static_items,
                                                 extra_filters=self.list_generator.extra_filters,
                                                 filters=list_config['filters'])

    def _process_POST(self):
        self.list_generator.store_configuration()
        return jsonify_data(flash=False, **self.list_generator.render_list())


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
            if isinstance(data['submitted_for_tracks'], Track):
                data['submitted_for_tracks'] = {data['submitted_for_tracks']}
            elif data['submitted_for_tracks'] is None:
                data['submitted_for_tracks'] = set()
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


class RHAbstractsDownloadAttachments(RHManageAbstractsActionsBase, ZipGeneratorMixin):
    """Generate a ZIP file with attachment files for a given list of abstracts"""

    def _prepare_folder_structure(self, item):
        abstract_title = secure_filename('{}_{}'.format(item.abstract.title, unicode(item.abstract.id)), 'abstract')
        file_name = secure_filename('{}_{}'.format(unicode(item.id), item.filename), item.filename)
        return os.path.join(*self._adjust_path_length([abstract_title, file_name]))

    def _iter_items(self, abstracts):
        for abstract in abstracts:
            for f in abstract.files:
                yield f

    def _process(self):
        return self._generate_zip_file(self.abstracts, name_prefix='abstract-attachments',
                                       name_suffix=self.event_new.id)


class RHAbstractsExportPDF(RHManageAbstractsActionsBase):
    def _process(self):
        sorted_abstracts = sorted(self.abstracts, key=attrgetter('friendly_id'))
        pdf = ConfManagerAbstractsToPDF(self.event_new, sorted_abstracts)
        return send_file('abstracts.pdf', pdf.generate(), 'application/pdf')
