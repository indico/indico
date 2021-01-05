# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import codecs
import os
import subprocess
import tempfile
from io import BytesIO
from operator import attrgetter
from zipfile import ZipFile

import markdown
import pkg_resources
from flask import session
from flask.helpers import get_root_path
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from jinja2.ext import Extension
from jinja2.lexer import Token
from pytz import timezone

from indico.core.config import config
from indico.core.logger import Logger
from indico.legacy.pdfinterface.base import escape
from indico.modules.events.abstracts.models.abstracts import AbstractReviewingState, AbstractState
from indico.modules.events.abstracts.models.reviews import AbstractAction
from indico.modules.events.abstracts.settings import BOACorrespondingAuthorType, boa_settings
from indico.modules.events.contributions.util import sort_contribs
from indico.modules.events.util import create_event_logo_tmp_file
from indico.util import mdx_latex
from indico.util.date_time import format_date, format_human_timedelta, format_time
from indico.util.fs import chmod_umask
from indico.util.i18n import _, ngettext
from indico.util.string import render_markdown
from indico.web.flask.templating import EnsureUnicodeExtension


class PDFLaTeXBase(object):
    _table_of_contents = False
    LATEX_TEMPLATE = None

    def __init__(self):
        # Markdown -> LaTeX renderer
        # safe_mode - strip out all HTML
        md = markdown.Markdown(safe_mode='remove')
        self.source_dir = tempfile.mkdtemp(prefix='indico-texgen-', dir=config.TEMP_DIR)
        latex_mdx = mdx_latex.LaTeXExtension(configs={'apply_br': True, 'tmpdir': self.source_dir})
        latex_mdx.extendMarkdown(md, markdown.__dict__)

        def _escape_latex_math(string):
            return mdx_latex.latex_escape(string, ignore_math=True)

        def _convert_markdown(text):
            return RawLatex(render_markdown(text, md=md.convert, escape_latex_math=_escape_latex_math))

        self._args = {'markdown': _convert_markdown}

    def generate(self):
        latex = LatexRunner(self.source_dir, has_toc=self._table_of_contents)
        return latex.run(self.LATEX_TEMPLATE, **self._args)

    def generate_source_archive(self):
        latex = LatexRunner(self.source_dir, has_toc=self._table_of_contents)
        latex.prepare(self.LATEX_TEMPLATE, **self._args)

        buf = BytesIO()
        with ZipFile(buf, 'w', allowZip64=True) as zip_handler:
            for dirpath, dirnames, files in os.walk(self.source_dir, followlinks=True):
                for f in files:
                    if f.startswith('.') or f.endswith(('.py', '.pyc', '.pyo')):
                        continue
                    file_path = os.path.join(dirpath, f)
                    archive_name = os.path.relpath(file_path, self.source_dir).encode('utf-8')
                    zip_handler.write(os.path.abspath(file_path), archive_name)
        buf.seek(0)
        return buf


class LaTeXRuntimeException(Exception):
    def __init__(self, source_file, log_file):
        super(LaTeXRuntimeException, self).__init__('LaTeX compilation of {} failed'.format(source_file))
        self.source_file = source_file
        self.log_file = log_file

    @property
    def message(self):
        return "Could not compile '{}'. Read '{}' for details".format(self.source_file, self.log_file)


class LatexEscapeExtension(Extension):
    """Ensure all strings in Jinja are latex-escaped."""

    def filter_stream(self, stream):
        in_trans = False
        in_variable = False
        for token in stream:
            # Check if we are inside a trans block - we cannot use filters there!
            if token.type == 'block_begin':
                block_name = stream.current.value
                if block_name == 'trans':
                    in_trans = True
                elif block_name == 'endtrans':
                    in_trans = False
            elif token.type == 'variable_begin':
                in_variable = True

            if in_variable and not in_trans:
                if token.type == 'variable_end' or (token.type == 'name' and token.value == 'if'):
                    yield Token(token.lineno, 'pipe', '|')
                    yield Token(token.lineno, 'name', 'latex')

            if token.type == 'variable_end':
                in_variable = False

            # Original token
            yield token


class RawLatex(unicode):
    pass


def _latex_escape(s, ignore_braces=False):
    if not isinstance(s, basestring) or isinstance(s, RawLatex):
        return s
    if isinstance(s, str):
        s = s.decode('utf-8')
    return RawLatex(mdx_latex.latex_escape(s, ignore_braces=ignore_braces))


class LatexRunner(object):
    """Handle the PDF generation from a chosen LaTeX template."""

    def __init__(self, source_dir, has_toc=False):
        self.source_dir = source_dir
        self.has_toc = has_toc

    def run_latex(self, source_file, log_file=None):
        pdflatex_cmd = [config.XELATEX_PATH,
                        '-no-shell-escape',
                        '-interaction', 'nonstopmode',
                        '-output-directory', self.source_dir,
                        os.path.relpath(source_file, self.source_dir)]

        try:
            # set config which limits location of input/output files
            subprocess.check_call(
                pdflatex_cmd,
                stdout=log_file,
                cwd=self.source_dir,
                env=dict(os.environ, TEXMFCNF='{}:'.format(os.path.dirname(__file__)))
            )
            Logger.get('pdflatex').debug("PDF created successfully!")

        except subprocess.CalledProcessError:
            Logger.get('pdflatex').debug('PDF creation possibly failed (non-zero exit code)!')
            # Only fail if we are in strict mode
            if config.STRICT_LATEX:
                # flush log, go to beginning and read it
                if log_file:
                    log_file.flush()
                raise

    def _render_template(self, template_name, kwargs):
        template_dir = os.path.join(get_root_path('indico'), 'legacy/pdfinterface/latex_templates')
        env = Environment(loader=FileSystemLoader(template_dir),
                          autoescape=False,
                          trim_blocks=True,
                          keep_trailing_newline=True,
                          auto_reload=config.DEBUG,
                          extensions=[LatexEscapeExtension],
                          undefined=StrictUndefined,
                          block_start_string=r'\JINJA{', block_end_string='}',
                          variable_start_string=r'\VAR{', variable_end_string='}',
                          comment_start_string=r'\#{', comment_end_string='}')
        env.filters['format_date'] = EnsureUnicodeExtension.wrap_func(format_date)
        env.filters['format_time'] = EnsureUnicodeExtension.wrap_func(format_time)
        env.filters['format_duration'] = lambda delta: format_human_timedelta(delta, 'minutes')
        env.filters['latex'] = _latex_escape
        env.filters['rawlatex'] = RawLatex
        env.filters['markdown'] = kwargs.pop('markdown')
        env.globals['_'] = _
        env.globals['ngettext'] = ngettext
        env.globals['session'] = session
        template = env.get_or_select_template(template_name)
        return template.render(font_dir='fonts/', **kwargs)

    def prepare(self, template_name, **kwargs):
        chmod_umask(self.source_dir, execute=True)
        source_filename = os.path.join(self.source_dir, template_name + '.tex')
        target_filename = os.path.join(self.source_dir, template_name + '.pdf')

        source = self._render_template(template_name + '.tex', kwargs)
        with codecs.open(source_filename, 'wb', encoding='utf-8') as f:
            f.write(source)

        distribution = pkg_resources.get_distribution('indico-fonts')
        font_dir = os.path.join(distribution.location, 'indico_fonts')
        os.symlink(font_dir, os.path.join(self.source_dir, 'fonts'))
        return source_filename, target_filename

    def run(self, template_name, **kwargs):
        if not config.LATEX_ENABLED:
            raise RuntimeError('LaTeX is not enabled')
        source_filename, target_filename = self.prepare(template_name, **kwargs)
        log_filename = os.path.join(self.source_dir, 'output.log')
        log_file = open(log_filename, 'a+')
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
    LATEX_TEMPLATE = 'single_doc'

    def __init__(self, abstract, tz=None):
        super(AbstractToPDF, self).__init__()

        self._abstract = abstract
        event = abstract.event

        if tz is None:
            tz = event.timezone

        self._args.update({
            'doc_type': 'abstract',
            'management': False,
            'abstract': abstract,
            'event': event,
            'tz': timezone(tz),
            'track_class': self._get_track_classification(abstract),
            'contrib_type': self._get_contrib_type(abstract),
            'link_format': boa_settings.get(event, 'link_format'),
        })
        self._args['logo_img'] = create_event_logo_tmp_file(event, self.source_dir) if event.logo else None

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
    LATEX_TEMPLATE = 'report'

    def __init__(self, event, abstracts, tz=None):
        super(AbstractsToPDF, self).__init__()
        if tz is None:
            self._tz = event.timezone

        self._args.update({
            'event': event,
            'doc_type': 'abstract',
            'management': False,
            'title': _("Report of Abstracts"),
            'get_track_classification': AbstractToPDF._get_track_classification,
            'get_contrib_type': AbstractToPDF._get_contrib_type,
            'items': abstracts,
            'url': event.short_external_url,
            'link_format': boa_settings.get(event, 'link_format'),
        })

        self._args['logo_img'] = create_event_logo_tmp_file(event, self.source_dir) if event.logo else None


class ConfManagerAbstractToPDF(AbstractToPDF):
    def __init__(self, abstract, tz=None):
        super(ConfManagerAbstractToPDF, self).__init__(abstract, tz)

        self._args.update({
            'management': True,
            'status': self._get_status(abstract),
            'track_judgments': self._get_track_reviewing_states(abstract)
        })

    @staticmethod
    def _get_status(abstract):
        state_title = abstract.state.title.upper()
        if abstract.state == AbstractState.duplicate:
            return u"{} (#{}: {})".format(state_title, abstract.duplicate_of.friendly_id, abstract.duplicate_of.title)
        elif abstract.state == AbstractState.merged:
            return u"{} (#{}: {})".format(state_title, abstract.merged_into.friendly_id, abstract.merged_into.title)
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
            'management': True,
            'get_status': ConfManagerAbstractToPDF._get_status,
            'get_track_judgments': ConfManagerAbstractToPDF._get_track_reviewing_states
        })


class ContribToPDF(PDFLaTeXBase):
    LATEX_TEMPLATE = 'single_doc'

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
            'link_format': boa_settings.get(event, 'link_format'),
        })

        self._args['logo_img'] = create_event_logo_tmp_file(event, self.source_dir) if event.logo else None


class ContribsToPDF(PDFLaTeXBase):
    _table_of_contents = True
    LATEX_TEMPLATE = 'report'

    def __init__(self, event, contribs, tz=None):
        super(ContribsToPDF, self).__init__()

        self._args.update({
            'doc_type': 'contribution',
            'title': _("Report of Contributions"),
            'event': event,
            'items': contribs,
            'url': event.short_external_url,
            'tz': timezone(tz or event.timezone),
            'link_format': boa_settings.get(event, 'link_format'),
        })

        self._args['logo_img'] = create_event_logo_tmp_file(event, self.source_dir) if event.logo else None


class ContributionBook(PDFLaTeXBase):
    LATEX_TEMPLATE = 'contribution_list_book'

    def __init__(self, event, user, contribs=None, tz=None, sort_by=""):
        super(ContributionBook, self).__init__()

        tz = tz or event.timezone
        contribs = sort_contribs(contribs or event.contributions, sort_by)
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
                corresp_authors[contrib.id] = [pl.person.email for pl in contrib.person_links
                                               if pl.is_submitter and pl.person.email]
            if boa_settings.get(event, 'corresponding_author') == BOACorrespondingAuthorType.speakers:
                corresp_authors[contrib.id] = [speaker.person.email for speaker in contrib.speakers
                                               if speaker.person.email]

        self._args.update({
            'affiliation_contribs': affiliation_contribs,
            'corresp_authors': corresp_authors,
            'contribs': contribs,
            'event': event,
            'tz': timezone(tz or event.timezone),
            'url': event.url,
            'sorted_by': sort_by,
            'user': user,
            'boa_text': boa_settings.get(event, 'extra_text'),
            'boa_text_end': boa_settings.get(event, 'extra_text_end'),
            'min_lines_per_abstract': boa_settings.get(event, 'min_lines_per_abstract'),
            'link_format': boa_settings.get(event, 'link_format'),
        })

        self._args['logo_img'] = create_event_logo_tmp_file(event, self.source_dir) if event.logo else None


class AbstractBook(ContributionBook):
    LATEX_TEMPLATE = 'book_of_abstracts'
    _table_of_contents = True

    def __init__(self, event, tz=None):
        sort_by = boa_settings.get(event, 'sort_by')
        super(AbstractBook, self).__init__(event, None, sort_by=sort_by)
        self._args['show_ids'] = boa_settings.get(event, 'show_abstract_ids')
        self._args['url'] = None
