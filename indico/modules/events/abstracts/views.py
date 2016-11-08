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

from flask import render_template, session

from MaKaC.common.TemplateExec import render
from MaKaC.webinterface.pages.base import WPJinjaMixin
from MaKaC.webinterface.pages.conferences import WPConferenceDefaultDisplayBase, WPConferenceModifBase


class WPManageAbstracts(WPJinjaMixin, WPConferenceModifBase):
    template_prefix = 'events/abstracts/'
    sidemenu_option = 'abstracts'

    def getJSFiles(self):
        return (WPConferenceModifBase.getJSFiles(self) +
                self._asset_env['markdown_js'].urls() +
                self._asset_env['selectize_js'].urls() +
                self._asset_env['modules_abstracts_js'].urls())

    def getCSSFiles(self):
        return (WPConferenceModifBase.getCSSFiles(self) +
                self._asset_env['markdown_sass'].urls() +
                self._asset_env['selectize_css'].urls() +
                self._asset_env['abstracts_sass'].urls())

    def _getHeadContent(self):
        return (WPConferenceModifBase._getHeadContent(self) + render('js/mathjax.config.js.tpl') +
                '\n'.join('<script src="{0}" type="text/javascript"></script>'.format(url)
                          for url in self._asset_env['mathjax_js'].urls()))


class WPDisplayAbstractsBase(WPJinjaMixin, WPConferenceDefaultDisplayBase):
    template_prefix = 'events/abstracts/'

    def getJSFiles(self):
        return (WPConferenceDefaultDisplayBase.getJSFiles(self) +
                self._asset_env['markdown_js'].urls() +
                self._asset_env['selectize_js'].urls() +
                self._asset_env['modules_abstracts_js'].urls())

    def getCSSFiles(self):
        return (WPConferenceDefaultDisplayBase.getCSSFiles(self) +
                self._asset_env['markdown_sass'].urls() +
                self._asset_env['selectize_css'].urls() +
                self._asset_env['abstracts_sass'].urls() +
                self._asset_env['event_display_sass'].urls() +
                self._asset_env['contributions_sass'].urls())

    def _getBody(self, params):
        return WPJinjaMixin._getPageContent(self, params).encode('utf-8')

    def _getHeadContent(self):
        return (WPConferenceDefaultDisplayBase._getHeadContent(self) + render('js/mathjax.config.js.tpl') +
                '\n'.join('<script src="{0}" type="text/javascript"></script>'.format(url)
                          for url in self._asset_env['mathjax_js'].urls()))


class WPDisplayAbstracts(WPDisplayAbstractsBase):
    menu_entry_name = 'call_for_abstracts'


class WPMyAbstracts(WPDisplayAbstractsBase):
    menu_entry_name = 'user_abstracts'


class WPSubmitAbstract(WPDisplayAbstractsBase):
    menu_entry_name = 'abstract_submission'


class WPDisplayAbstractsReviewing(WPDisplayAbstracts):
    menu_entry_name = 'user_tracks'

    def getJSFiles(self):
        return (WPDisplayAbstracts.getJSFiles(self) +
                self._asset_env['modules_event_management_js'].urls())

    def getCSSFiles(self):
        return (WPDisplayAbstracts.getCSSFiles(self) +
                self._asset_env['event_display_sass'].urls() +
                self._asset_env['tracks_sass'].urls())


def render_abstract_page(abstract, view_class=None, management=False):
    from indico.modules.events.abstracts.forms import (AbstractCommentForm, AbstractJudgmentForm,
                                                       AbstractReviewedForTracksForm, build_review_form)
    comment_form = AbstractCommentForm(abstract=abstract, user=session.user, formdata=None)
    review_forms = {track.id: build_review_form(abstract, track)
                    for track in abstract.reviewed_for_tracks
                    if track.can_review_abstracts(session.user)}
    judgment_form = AbstractJudgmentForm(abstract=abstract, formdata=None)
    review_track_list_form = AbstractReviewedForTracksForm(event=abstract.event_new, obj=abstract, formdata=None)
    params = {'abstract': abstract,
              'comment_form': comment_form,
              'review_forms': review_forms,
              'review_track_list_form': review_track_list_form,
              'judgment_form': judgment_form,
              'management': management}
    if view_class:
        return view_class.render_template('abstract.html', abstract.event_new.as_legacy, **params)
    else:
        return render_template('events/abstracts/abstract.html', no_javascript=True, **params)
