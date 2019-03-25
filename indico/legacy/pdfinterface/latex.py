# This file is part of Indico.
# Copyright (C) 2002 - 2019 European Organization for Nuclear Research (CERN).
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
import subprocess
import tempfile
from operator import attrgetter

import markdown
from flask.helpers import get_root_path
from pytz import timezone

from indico.core.config import config
from indico.core.logger import Logger
from indico.legacy.common.TemplateExec import render as tpl_render
from indico.legacy.pdfinterface.base import escape
from indico.modules.events.abstracts.models.abstracts import AbstractReviewingState, AbstractState
from indico.modules.events.abstracts.models.reviews import AbstractAction
from indico.modules.events.abstracts.settings import BOACorrespondingAuthorType, BOASortField, boa_settings
from indico.modules.events.util import create_event_logo_tmp_file
from indico.util import mdx_latex
from indico.util.fs import chmod_umask
from indico.util.i18n import _
from indico.util.string import render_markdown


class PDFLaTeXBase(object):
    _table_of_contents = False

    def __init__(self):
        # Markdown -> LaTeX renderer
        # safe_mode - strip out all HTML
        md = markdown.Markdown(safe_mode='remove')
        latex_mdx = mdx_latex.LaTeXExtension(configs={'apply_br'})
        latex_mdx.extendMarkdown(md, markdown.__dict__)

        def _escape_latex_math(string):
            return mdx_latex.latex_escape(string, ignore_math=True)

        def _convert_markdown(text):
            return render_markdown(text, md=md.convert, escape_latex_math=_escape_latex_math)

        self._args = {'md_convert': _convert_markdown}

    def generate(self):
        latex = LatexRunner(has_toc=self._table_of_contents)
        return latex.run(self._tpl_filename, **self._args)


class LaTeXRuntimeException(Exception):
    def __init__(self, source_file, log_file):
        super(LaTeXRuntimeException, self).__init__('LaTeX compilation of {} failed'.format(source_file))
        self.source_file = source_file
        self.log_file = log_file

    @property
    def message(self):
        return "Could not compile '{}'. Read '{}' for details".format(self.source_file, self.log_file)


class LatexRunner(object):
    """Handles the PDF generation from a chosen LaTeX template"""

    def __init__(self, has_toc=False):
        self.has_toc = has_toc

    def run_latex(self, source_file, log_file=None):
        pdflatex_cmd = [config.XELATEX_PATH,
                        '-no-shell-escape',
                        '-interaction', 'nonstopmode',
                        '-output-directory', self._dir,
                        source_file]

        try:
            subprocess.check_call(pdflatex_cmd, stdout=log_file)
            Logger.get('pdflatex').debug("PDF created successfully!")

        except subprocess.CalledProcessError:
            Logger.get('pdflatex').warning('PDF creation possibly failed (non-zero exit code)!')
            # Only fail if we are in strict mode
            if config.STRICT_LATEX:
                # flush log, go to beginning and read it
                if log_file:
                    log_file.flush()
                raise

    def run(self, template_name, **kwargs):
        template_dir = os.path.join(get_root_path('indico'), 'legacy/webinterface/tpls/latex')
        template = tpl_render(os.path.join(template_dir, template_name), kwargs)

        self._dir = tempfile.mkdtemp(prefix="indico-texgen-", dir=config.TEMP_DIR)
        chmod_umask(self._dir, execute=True)
        source_filename = os.path.join(self._dir, template_name + '.tex')
        target_filename = os.path.join(self._dir, template_name + '.pdf')
        log_filename = os.path.join(self._dir, 'output.log')
        log_file = open(log_filename, 'a+')

        with open(source_filename, 'w') as f:
            f.write(template)

        try:
            self.run_latex(source_filename, log_file)
            if self.has_toc:
                self.run_latex(source_filename, log_file)
        finally:
            log_file.close()

            if not os.path.exists(target_filename):
                # something went terribly wrong, no LaTeX file was produced
                raise LaTeXRuntimeException(source_filename, log_filename)

        return target_filename


def extract_affiliations(contrib):
    affiliations = dict()

    def enumerate_affil(person_links):
        auth_list = []

        for person_link in person_links:
            affil = person_link.affiliation
            if affil and affil not in affiliations:
                affiliations[affil] = len(affiliations) + 1
            auth_list.append((person_link, affiliations[affil] if affil else None))
        return auth_list

    authors = enumerate_affil(contrib.primary_authors)
    coauthors = enumerate_affil(contrib.secondary_authors)
    return affiliations, authors, coauthors


class AbstractToPDF(PDFLaTeXBase):
    _tpl_filename = 'single_doc.tpl'

    def __init__(self, abstract, tz=None):
        super(AbstractToPDF, self).__init__()

        self._abstract = abstract
        event = abstract.event

        if tz is None:
            tz = event.timezone

        self._args.update({
            'doc_type': 'abstract',
            'abstract': abstract,
            'event': event,
            'tz': timezone(tz),
            'track_class': self._get_track_classification(abstract),
            'contrib_type': self._get_contrib_type(abstract),
            'fields': [f for f in event.contribution_fields if f.is_active]
        })
        if event.logo:
            self._args['logo_img'] = create_event_logo_tmp_file(event).name

    @staticmethod
    def _get_track_classification(abstract):
        if abstract.state == AbstractState.accepted:
            if abstract.accepted_track:
                return escape(abstract.accepted_track.full_title)
        else:
            tracks = sorted(abstract.submitted_for_tracks | abstract.reviewed_for_tracks, key=attrgetter('position'))
            return u'; '.join(escape(t.full_title) for t in tracks)

    @staticmethod
    def _get_contrib_type(abstract):
        is_accepted = abstract.state == AbstractState.accepted
        return abstract.accepted_contrib_type if is_accepted else abstract.submitted_contrib_type


class AbstractsToPDF(PDFLaTeXBase):
    _tpl_filename = "report.tpl"

    def __init__(self, event, abstracts, tz=None):
        super(AbstractsToPDF, self).__init__()
        if tz is None:
            self._tz = event.timezone

        self._args.update({
            'event': event,
            'doc_type': 'abstract',
            'title': _("Report of Abstracts"),
            'get_track_classification': AbstractToPDF._get_track_classification,
            'get_contrib_type': AbstractToPDF._get_contrib_type,
            'items': abstracts,
            'fields': [f for f in event.contribution_fields if f.is_active]
        })


class ConfManagerAbstractToPDF(AbstractToPDF):

    def __init__(self, abstract, tz=None):
        super(ConfManagerAbstractToPDF, self).__init__(abstract, tz)

        self._args.update({
            'doc_type': 'abstract_manager',
            'status': self._get_status(abstract),
            'track_judgements': self._get_track_reviewing_states(abstract)
        })

    @staticmethod
    def _get_status(abstract):
        state_title = abstract.state.title.upper()
        if abstract.state == AbstractState.duplicate:
            return _(u"{} (#{}: {})").format(state_title, abstract.duplicate_of.friendly_id,
                                             abstract.duplicate_of.title)
        elif abstract.state == AbstractState.merged:
            return _(u"{} (#{}: {})").format(state_title, abstract.merged_into.friendly_id, abstract.merged_into.title)
        else:
            return abstract.state.title.upper()

    @staticmethod
    def _get_track_reviewing_states(abstract):
        def _format_review_action(review):
            action = unicode(review.proposed_action.title)
            if review.proposed_action == AbstractAction.accept and review.proposed_contribution_type:
                return u'{}: {}'.format(action, review.proposed_contribution_type.name)
            else:
                return action

        reviews = []
        for track in abstract.reviewed_for_tracks:
            track_review_state = abstract.get_track_reviewing_state(track)
            review_state = track_review_state.title
            track_reviews = abstract.get_reviews(group=track)
            review_details = [(_format_review_action(review),
                               review.user.get_full_name(abbrev_first_name=False),
                               review.comment,
                               review.score,
                               [(rating.question.title, rating.value) for rating in review.ratings])
                              for review in track_reviews]
            if track_review_state in {AbstractReviewingState.positive, AbstractReviewingState.conflicting}:
                proposed_contrib_types = {r.proposed_contribution_type.name for r in track_reviews
                                          if r.proposed_contribution_type}
                if proposed_contrib_types:
                    contrib_types = u', '.join(proposed_contrib_types)
                    review_state = u'{}: {}'.format(review_state, contrib_types)
            elif track_review_state == AbstractReviewingState.mixed:
                other_tracks = {x.title for r in track_reviews for x in r.proposed_tracks}
                proposed_actions = {x.proposed_action for x in track_reviews}
                no_track_actions = proposed_actions - {AbstractAction.change_tracks}
                other_info = []
                if no_track_actions:
                    other_info.append(u', '.join(unicode(a.title) for a in no_track_actions))
                if other_tracks:
                    other_info.append(_(u"Proposed for other tracks: {}").format(u', '.join(other_tracks)))
                if other_info:
                    review_state = u'{}: {}'.format(review_state, u'; '.join(other_info))

            elif track_review_state not in {AbstractReviewingState.negative, AbstractReviewingState.conflicting}:
                continue
            reviews.append((track.title, review_state, review_details))
        return reviews


class ConfManagerAbstractsToPDF(AbstractsToPDF):

    def __init__(self, event, abstracts, tz=None):
        super(ConfManagerAbstractsToPDF, self).__init__(event, abstracts, tz)

        self._args.update({
            'doc_type': 'abstract_manager',
            'get_status': ConfManagerAbstractToPDF._get_status,
            'get_track_judgements': ConfManagerAbstractToPDF._get_track_reviewing_states
        })


class ContribToPDF(PDFLaTeXBase):
    _tpl_filename = 'single_doc.tpl'

    def __init__(self, contrib, tz=None):
        super(ContribToPDF, self).__init__()

        event = contrib.event
        affiliations, author_mapping, coauthor_mapping = extract_affiliations(contrib)

        self._args.update({
            'doc_type': 'contribution',
            'affiliations': affiliations,
            'authors_affil': author_mapping,
            'coauthors_affil': coauthor_mapping,
            'contrib': contrib,
            'event': event,
            'tz': timezone(tz or event.timezone),
            'fields': [f for f in event.contribution_fields if f.is_active]
        })

        if event.logo:
            self.temp_file = create_event_logo_tmp_file(event)
            self._args['logo_img'] = self.temp_file.name


class ContribsToPDF(PDFLaTeXBase):
    _table_of_contents = True
    _tpl_filename = "report.tpl"

    def __init__(self, event, contribs, tz=None):
        super(ContribsToPDF, self).__init__()

        self._args.update({
            'doc_type': 'contribution',
            'title': _("Report of Contributions"),
            'event': event,
            'items': contribs,
            'fields': [f for f in event.contribution_fields if f.is_active],
            'url': event.short_external_url,
            'tz': timezone(tz or event.timezone)
        })

        if event.logo:
            self.temp_file = create_event_logo_tmp_file(event)
            self._args['logo_img'] = self.temp_file.name


class ContributionBook(PDFLaTeXBase):
    _tpl_filename = "contribution_list_boa.tpl"

    def _sort_contribs(self, contribs, sort_by):
        mapping = {'number': 'id', 'name': 'title'}
        if sort_by == BOASortField.schedule:
            key_func = lambda c: (c.start_dt is None, c.start_dt)
        elif sort_by == BOASortField.session_title:
            key_func = lambda c: (c.session is None, c.session.title.lower() if c.session else '')
        elif sort_by == BOASortField.speaker:
            def key_func(c):
                speakers = c.speakers
                if not c.speakers:
                    return True, None
                return False, speakers[0].get_full_name(last_name_upper=False, abbrev_first_name=False).lower()
        else:
            key_func = attrgetter(mapping.get(sort_by) or 'title')
        return sorted(contribs, key=key_func)

    def __init__(self, event, user, contribs=None, tz=None, sort_by=""):
        super(ContributionBook, self).__init__()

        tz = tz or event.timezone
        contribs = self._sort_contribs(contribs or event.contributions, sort_by)
        affiliation_contribs = {}
        corresp_authors = {}

        for contrib in contribs:
            affiliations, author_mapping, coauthor_mapping = extract_affiliations(contrib)
            affiliation_contribs[contrib.id] = {
                'affiliations': affiliations,
                'authors_affil': author_mapping,
                'coauthors_affil': coauthor_mapping
            }

            # figure out "corresponding author(s)"
            if boa_settings.get(event, 'corresponding_author') == BOACorrespondingAuthorType.submitter:
                corresp_authors[contrib.id] = [pl.person.email for pl in contrib.person_links if pl.is_submitter]
            if boa_settings.get(event, 'corresponding_author') == BOACorrespondingAuthorType.speakers:
                corresp_authors[contrib.id] = [speaker.person.email for speaker in contrib.speakers]

        self._args.update({
            'affiliation_contribs': affiliation_contribs,
            'corresp_authors': corresp_authors,
            'contribs': contribs,
            'event': event,
            'tz': timezone(tz or event.timezone),
            'url': event.url,
            'fields': [f for f in event.contribution_fields if f.is_active],
            'sorted_by': sort_by,
            'user': user,
            'boa_text': boa_settings.get(event, 'extra_text')
        })

        if event.logo:
            self.temp_file = create_event_logo_tmp_file(event)
            self._args['logo_img'] = self.temp_file.name


class AbstractBook(ContributionBook):
    _tpl_filename = "book_of_abstracts.tpl"
    _table_of_contents = True

    def __init__(self, event, tz=None):
        sort_by = boa_settings.get(event, 'sort_by')

        super(AbstractBook, self).__init__(event, None, sort_by=sort_by)
        self._args['show_ids'] = boa_settings.get(event, 'show_abstract_ids')

        del self._args["url"]
