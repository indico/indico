# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import render_template, session

from indico.modules.events.abstracts.util import filter_field_values, get_visible_reviewed_for_tracks
from indico.modules.events.management.views import WPEventManagement
from indico.modules.events.views import WPConferenceDisplayBase
from indico.util.mathjax import MathjaxMixin


class WPManageAbstracts(MathjaxMixin, WPEventManagement):
    template_prefix = 'events/abstracts/'
    sidemenu_option = 'abstracts'
    bundles = ('module_events.abstracts.js', 'module_events.abstracts.css', 'markdown.js')

    def _get_head_content(self):
        return WPEventManagement._get_head_content(self) + MathjaxMixin._get_head_content(self)


class WPDisplayAbstractsBase(WPConferenceDisplayBase):
    template_prefix = 'events/abstracts/'
    bundles = ('module_events.abstracts.js', 'module_events.abstracts.css', 'markdown.js')


class WPDisplayAbstracts(WPDisplayAbstractsBase):
    menu_entry_name = 'call_for_abstracts'


class WPDisplayCallForAbstracts(WPDisplayAbstracts):
    pass


class WPDisplayAbstractsReviewing(WPDisplayAbstracts):
    menu_entry_name = 'abstract_reviewing_area'
    bundles = ('module_events.management.js',)


def render_abstract_page(abstract, view_class=None, management=False):
    from indico.modules.events.abstracts.forms import (AbstractCommentForm, AbstractJudgmentForm,
                                                       AbstractReviewedForTracksForm, build_review_form)
    comment_form = AbstractCommentForm(abstract=abstract, user=session.user, formdata=None)
    review_form = None
    reviewed_for_tracks = list(abstract.get_reviewed_for_groups(session.user))
    if len(reviewed_for_tracks) == 1:
        review_form = build_review_form(abstract, reviewed_for_tracks[0])
    judgment_form = AbstractJudgmentForm(abstract=abstract, formdata=None)
    review_track_list_form = AbstractReviewedForTracksForm(event=abstract.event, obj=abstract, formdata=None)
    track_session_map = {track.id: track.default_session_id for track in abstract.event.tracks}
    can_manage = abstract.event.can_manage(session.user)
    field_values = filter_field_values(abstract.field_values, can_manage, abstract.user_owns(session.user))
    params = {'abstract': abstract,
              'comment_form': comment_form,
              'review_form': review_form,
              'review_track_list_form': review_track_list_form,
              'judgment_form': judgment_form,
              'visible_tracks': get_visible_reviewed_for_tracks(abstract, session.user),
              'management': management,
              'track_session_map': track_session_map,
              'field_values': field_values}

    if view_class:
        return view_class.render_template('abstract.html', abstract.event, **params)
    else:
        return render_template('events/abstracts/abstract.html', no_javascript=True, standalone=True, **params)
