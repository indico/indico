# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

import errno
import os
from glob import glob
from urlparse import urlparse

import csscompressor
from flask.helpers import get_root_path
from markupsafe import Markup
from webassets import Bundle, Environment
from webassets.filter import Filter, register_filter
from webassets.filter.cssrewrite import CSSRewrite

from indico.core.config import config
from indico.modules.events.layout import theme_settings


SASS_BASE_MODULES = ["sass/*.scss", "sass/base/*.scss", "sass/custom/*.scss", "sass/partials/*.scss",
                     "sass/modules/*.scss", "sass/modules/*/*.scss"]


class CSSCompressor(Filter):
    name = 'csscompressor'

    def output(self, _in, out, **kw):
        out.write(csscompressor.compress(_in.read(), max_linelen=500))


class IndicoCSSRewrite(CSSRewrite):
    name = 'indico_cssrewrite'

    def __init__(self):
        super(IndicoCSSRewrite, self).__init__()
        self.base_url_path = urlparse(config.BASE_URL.rstrip('/')).path

    def replace_url(self, url):
        parsed = urlparse(url)
        if parsed.scheme or parsed.netloc:
            return url
        elif parsed.path.startswith('/'):
            # Prefix absolute urls with the base path. Like this we avoid
            # the mess that comes with relative URLs in CSS while still
            # supporting Indico running in a subdirectory (e.g. /indico)
            return self.base_url_path + url
        else:
            return super(IndicoCSSRewrite, self).replace_url(url)


# XXX: DO NOT move this to decorators. this function returns None,
# so super() calls using the decorated class name fail...
register_filter(CSSCompressor)
register_filter(IndicoCSSRewrite)


def _get_htdocs_path():
    return os.path.join(get_root_path('indico'), 'htdocs')


def configure_pyscss(environment):
    base_url_path = urlparse(config.BASE_URL).path
    environment.config['PYSCSS_STYLE'] = 'compact'
    environment.config['PYSCSS_DEBUG_INFO'] = False
    environment.config['PYSCSS_STATIC_URL'] = '{0}/static/'.format(base_url_path)
    environment.config['PYSCSS_LOAD_PATHS'] = [
        os.path.join(_get_htdocs_path(), 'sass', 'lib', 'compass'),
        os.path.join(_get_htdocs_path(), 'sass')
    ]


def get_webassets_cache_dir(plugin_name=None):
    suffix = 'core' if not plugin_name else 'plugin-{}'.format(plugin_name)
    return os.path.join(config.CACHE_DIR, 'webassets-{}-{}'.format(config.WORKER_NAME, suffix))


class LazyCacheEnvironment(Environment):
    def _get_cache(self):
        # Create the cache dir if it doesn't exist. Like this we wait until
        # it is actually accessed instead of doing it at import time.
        # Not sure why webassets only lazily creates the cache dir when using
        # the default path but not when using a custom one...
        if isinstance(self._storage['cache'], basestring):
            try:
                os.mkdir(self._storage['cache'])
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise
        return Environment.cache.fget(self)
    cache = property(_get_cache, Environment.cache.fset)
    del _get_cache


class IndicoEnvironment(LazyCacheEnvironment):
    def init_app(self, app):
        self.config.update({'cache': get_webassets_cache_dir()})
        url_path = urlparse(config.BASE_URL).path
        self.directory = os.path.join(config.ASSETS_DIR, 'core')
        self.url = '{0}/static/assets/core/'.format(url_path)
        self.debug = app.debug
        configure_pyscss(self)
        self.append_path(_get_htdocs_path(), '/')
        self.append_path(os.path.join(_get_htdocs_path(), 'css'), '{0}/css'.format(url_path))
        self.append_path(os.path.join(_get_htdocs_path(), 'js'), '{0}/js'.format(url_path))


class ThemeEnvironment(LazyCacheEnvironment):
    def __init__(self, theme_id, theme):
        plugin = theme.get('plugin')
        url_path = urlparse(config.BASE_URL).path
        output_dir = os.path.join(config.ASSETS_DIR, 'theme-{}'.format(theme_id))
        output_url = '{}/static/assets/theme-{}'.format(url_path, theme_id)
        theme_root = plugin.root_path if plugin else os.path.join(_get_htdocs_path(), 'sass')
        static_dir = os.path.join(theme_root, 'themes')
        static_url = '{}/static/themes/{}'.format(url_path, theme_id)
        cache_dir = get_webassets_cache_dir(plugin.name if plugin else None)
        super(ThemeEnvironment, self).__init__(output_dir, output_url, debug=config.DEBUG, cache=cache_dir)
        self.append_path(output_dir, output_url)
        self.append_path(static_dir, static_url)
        self.append_path(_get_htdocs_path(), '/')
        configure_pyscss(self)


def namespace(dir_ns, *list_files):
    return [os.path.join(dir_ns, f) for f in list_files]


def include_js_assets(bundle_name):
    """Jinja template function to generate HTML tags for a JS asset bundle."""
    return Markup('\n'.join('<script src="{}"></script>'.format(url) for url in core_env[bundle_name].urls()))


def include_css_assets(bundle_name):
    """Jinja template function to generate HTML tags for a CSS asset bundle."""
    return Markup('\n'.join('<link rel="stylesheet" type="text/css" href="{}">'.format(url)
                            for url in core_env[bundle_name].urls()))


def rjs_bundle(name, *files, **kwargs):
    filters = kwargs.pop('filters', 'rjsmin')
    return Bundle(*files, filters=filters, output='js/{}_%(version)s.min.js'.format(name))


def _get_custom_files(subdir, pattern):
    customization_dir = config.CUSTOMIZATION_DIR
    if not customization_dir:
        return []
    customization_dir = os.path.join(customization_dir, subdir)
    if not os.path.exists(customization_dir):
        return []
    return sorted(glob(os.path.join(customization_dir, pattern)))


def register_all_js(env):
    indico_core = rjs_bundle(
        'indico_core',
        *namespace('js/indico/Core',
                   'Presentation.js',
                   'Data.js',
                   'Components.js',
                   'Auxiliar.js',
                   'Buttons.js',
                   'Effects.js',
                   'Interaction/Base.js',
                   'Widgets/Base.js',
                   'Widgets/Inline.js',
                   'Widgets/Menu.js',
                   'Widgets/RichText.js',
                   'Dialogs/Popup.js',
                   'Dialogs/PopupWidgets.js',
                   'Dialogs/Base.js',
                   'Dialogs/Util.js',
                   'Dialogs/Users.js',
                   'Dialogs/PopupWidgets.js',
                   'Browser.js',
                   'Util.js',
                   'Dragndrop.js',
                   'keymap.js'))

    indico_management = rjs_bundle(
        'indico_management',
        *namespace('js/indico/Management',
                   'RoomBooking.js',
                   'RoomBookingMapOfRooms.js'))

    indico_room_booking = rjs_bundle(
        'indico_room_booking',
        'js/lib/rrule.js',
        *namespace('js/indico/RoomBooking',
                   'util.js',
                   'MapOfRooms.js',
                   'BookingForm.js',
                   'RoomBookingCalendar.js',
                   'roomselector.js',
                   'validation.js'))

    indico_legacy = rjs_bundle(
        'indico_legacy',
        *namespace('js/indico/Legacy',
                   'Widgets.js',
                   'Util.js'))

    indico_common = rjs_bundle(
        'indico_common',
        *namespace('js/indico/Common',
                   'Export.js'))

    indico_jquery = rjs_bundle(
        'indico_jquery',
        *namespace('js/indico/jquery',
                   'defaults.js',
                   'global.js',
                   'declarative.js',
                   'errors.js',
                   'ajaxcheckbox.js',
                   'ajaxdialog.js',
                   'ajaxform.js',
                   'clearableinput.js',
                   'dropdown.js',
                   'actioninput.js',
                   'multitextfield.js',
                   'multiselect.js',
                   'principalfield.js',
                   'qbubble.js',
                   'ajaxqbubble.js',
                   'realtimefilter.js',
                   'scrollblocker.js',
                   'timerange.js',
                   'tooltips.js',
                   'nullableselector.js',
                   'colorpicker.js',
                   'palettepicker.js',
                   'itempicker.js',
                   'sortablelist.js',
                   'categorynavigator.js',
                   'track_role_widget.js',
                   'paper_email_settings_widget.js',
                   'permissions_widget.js'))

    indico_regform = rjs_bundle(
        'indico_regform',
        *namespace('js/indico/modules/registration/form',
                   'form.js',
                   'section.js',
                   'field.js',
                   'sectiontoolbar.js',
                   'table.js'))

    angular = rjs_bundle(
        'angular',
        'js/lib/angular.js',
        'js/lib/angular-resource.js',
        'js/lib/angular-sanitize.js',
        'js/lib/sortable.js',
        'js/indico/angular/app.js',
        'js/indico/angular/directives.js',
        'js/indico/angular/filters.js',
        'js/indico/angular/services.js')

    ckeditor = rjs_bundle('ckeditor', 'js/lib/ckeditor/ckeditor.js', filters=None)

    chartist_js = rjs_bundle('chartist_js',
                             'js/lib/chartist.js/chartist.js')

    clipboard_js = rjs_bundle('clipboard_js',
                              'js/lib/clipboard.js/clipboard.js',
                              'js/custom/clipboard.js')

    selectize_js = rjs_bundle('selectize_js',
                              'js/lib/selectize.js/selectize.js')
    taggle_js = rjs_bundle('taggle_js', 'js/lib/taggle.js')
    fullcalendar_js = rjs_bundle('fullcalendar_js', 'js/lib/fullcalendar.js')
    outdated_browser_js = rjs_bundle('outdated_browser_js', 'js/lib/outdatedbrowser.js')
    typewatch_js = rjs_bundle('typewatch_js', 'js/lib/jquery.typewatch.js')

    palette = rjs_bundle('palette', 'js/palette.js')

    _jquery_files = namespace('js/jquery',
                              'jquery.form.js',
                              'jquery.custom.js',
                              'jquery.daterange.js',
                              'jquery.dttbutton.js',
                              'jquery.colorbox.js',
                              'date.js',
                              'jquery.colorpicker.js',
                              'jquery-extra-selectors.js',
                              'jstorage.js')
    jquery = rjs_bundle('jquery', *filter(None, [
        'js/jquery/jquery-ui.js',
        'js/lib/jquery.multiselect.js',
        'js/lib/jquery.multiselect.filter.js',
        'js/lib/jquery.typeahead.js',
        'js/lib/jquery.tablesorter.js',
        'js/jquery/jquery-migrate-silencer.js' if not config.DEBUG else None] + _jquery_files))

    utils = rjs_bundle('utils', *namespace('js/utils', 'routing.js', 'misc.js', 'forms.js'))
    calendar = rjs_bundle('calendar', *namespace('js/calendar', 'calendar.js', 'calendar-setup.js'))

    presentation = rjs_bundle(
        'presentation',
        *namespace('js/presentation',

                   'Core/Primitives.js',
                   'Core/Iterators.js',
                   'Core/Tools.js',
                   'Core/String.js',
                   'Core/Type.js',
                   'Core/Interfaces.js',
                   'Core/Commands.js',
                   'Core/MathEx.js',
                   'Data/Bag.js',
                   'Data/WatchValue.js',
                   'Data/WatchList.js',
                   'Data/WatchObject.js',
                   'Data/Binding.js',
                   'Data/Logic.js',
                   'Data/Json.js',
                   'Data/Remote.js',
                   'Data/DateTime.js',
                   'Ui/XElement.js',
                   'Ui/Html.js',
                   'Ui/Dom.js',
                   'Ui/Extensions/Layout.js',
                   'Ui/Text.js',
                   'Ui/Widgets/WidgetBase.js',
                   'Ui/Widgets/WidgetComponents.js',
                   'Ui/Widgets/WidgetControl.js'))

    mathjax_js = rjs_bundle('mathjax', 'js/lib/mathjax/MathJax.js', 'js/custom/pagedown_mathjax.js')

    markdown_js = rjs_bundle(
        'markdown',
        *namespace('js/lib/pagedown',
                   'Markdown.Converter.js',
                   'Markdown.Editor.js',
                   'Markdown.Sanitizer.js'))

    module_js = {
        'global': rjs_bundle('modules_global', *namespace('js/indico/modules/global',
                                                          'session_bar.js', 'impersonation.js')),
        'bootstrap': rjs_bundle('modules_bootstrap', 'js/indico/modules/bootstrap.js'),
        'cephalopod': rjs_bundle('modules_cephalopod', 'js/indico/modules/cephalopod.js'),
        'categories': rjs_bundle('modules_categories', *namespace('js/indico/modules/categories', 'display.js',
                                                                  'calendar.js')),
        'categories_management': rjs_bundle('modules_categories_management',
                                            'js/indico/modules/categories/management.js'),
        'vc': rjs_bundle('modules_vc', 'js/indico/modules/vc.js'),
        'event_creation': rjs_bundle('modules_event_creation', 'js/indico/modules/events/creation.js'),
        'event_display': rjs_bundle('modules_event_display', *namespace('js/indico/modules', 'events/display.js',
                                                                        'list_generator.js', 'static_filters.js',
                                                                        'social.js')),
        'event_layout': rjs_bundle('modules_event_layout', 'js/indico/modules/events/layout.js'),
        'event_management': rjs_bundle('modules_event_management',
                                       *namespace('js/indico/modules', 'events/management.js', 'events/badges.js',
                                                  'list_generator.js', 'static_filters.js')),
        'attachments': rjs_bundle('modules_attachments', 'js/indico/modules/attachments.js'),
        'surveys': rjs_bundle('modules_surveys', 'js/indico/modules/surveys.js'),
        'registration': rjs_bundle('modules_registration',
                                   'js/indico/modules/registration/registration.js',
                                   'js/indico/modules/registration/invitations.js',
                                   'js/indico/modules/registration/reglists.js',
                                   *namespace('js/indico/modules/registration/form', 'form.js', 'section.js',
                                              'field.js',
                                              'sectiontoolbar.js', 'table.js')),
        'contributions': rjs_bundle('modules_contributions', 'js/indico/modules/contributions/common.js',
                                    'js/indico/modules/types_dialog.js'),
        'tracks': rjs_bundle('modules_tracks', 'js/indico/modules/tracks.js'),
        'abstracts': rjs_bundle('modules_abstracts',
                                'js/indico/modules/abstracts.js',
                                'js/indico/modules/types_dialog.js',
                                'js/indico/jquery/rulelistwidget.js'),
        'papers': rjs_bundle('modules_papers', 'js/indico/modules/papers.js'),
        'reviews': rjs_bundle('modules_reviews', 'js/indico/modules/reviews.js'),
        'timetable': rjs_bundle('modules_timetable',
                                *namespace('js/indico/modules/timetable/timetable', 'Management.js', 'Filter.js',
                                           'Layout.js', 'Undo.js', 'Base.js', 'DragAndDrop.js', 'Draw.js',
                                           'Actions.js')),
        'sessions': rjs_bundle('modules_sessions', 'js/indico/modules/sessions/common.js',
                               'js/indico/modules/types_dialog.js'),
        'users': rjs_bundle('modules_users', 'js/indico/modules/users.js'),
        'designer': rjs_bundle('modules_designer', 'js/indico/modules/designer.js'),
        'event_cloning': rjs_bundle('modules_event_cloning', 'js/indico/modules/events/cloning.js'),
        'event_roles': rjs_bundle('modules_event_roles', 'js/indico/modules/events/roles.js')
    }

    widgets_js = rjs_bundle('widgets', *namespace('js/indico/widgets',
                                                  'category_picker_widget.js',
                                                  'ckeditor_widget.js',
                                                  'color_picker_widget.js',
                                                  'datetime_widget.js',
                                                  'linking_widget.js',
                                                  'location_widget.js',
                                                  'markdown_widget.js',
                                                  'multiple_items_widget.js',
                                                  'occurrences_widget.js',
                                                  'override_multiple_items_widget.js',
                                                  'person_link_widget.js',
                                                  'principal_list_widget.js',
                                                  'principal_widget.js',
                                                  'protection_widget.js',
                                                  'selectize_widget.js',
                                                  'synced_input_widget.js',
                                                  'typeahead_widget.js'))

    base_js = Bundle(palette, jquery, angular, utils, presentation, calendar, indico_jquery,
                     indico_core, indico_legacy, indico_common, clipboard_js, taggle_js, typewatch_js, fullcalendar_js,
                     outdated_browser_js, widgets_js, module_js['event_creation'], module_js['global'])

    env.register('jquery', jquery)
    env.register('utils', utils)
    env.register('presentation', presentation)
    env.register('indico_core', indico_core)
    env.register('indico_management', indico_management)
    env.register('indico_roombooking', indico_room_booking)
    env.register('indico_legacy', indico_legacy)
    env.register('indico_common', indico_common)
    env.register('indico_jquery', indico_jquery)
    env.register('indico_regform', indico_regform)
    env.register('base_js', base_js)
    env.register('mathjax_js', mathjax_js)
    env.register('markdown_js', markdown_js)
    env.register('clipboard_js', clipboard_js)
    env.register('selectize_js', selectize_js)
    env.register('ckeditor', ckeditor)
    env.register('chartist_js', chartist_js)
    env.register('taggle_js', taggle_js)
    env.register('widgets_js', widgets_js)
    for key, bundle in module_js.iteritems():
        env.register('modules_{}_js'.format(key), bundle)
    # Build a bundle with customization JS if enabled
    custom_js_files = _get_custom_files('js', '*.js')
    if custom_js_files:
        env.register('custom_js', rjs_bundle('custom', *custom_js_files))


def register_theme_sass():
    for theme_id, data in theme_settings.themes.viewitems():
        stylesheet = data['stylesheet']
        if stylesheet:
            bundle = Bundle('css/events/common.css',
                            stylesheet,
                            filters=('pyscss', 'indico_cssrewrite', 'csscompressor'),
                            output='{}_%(version)s.css'.format(theme_id),
                            depends=SASS_BASE_MODULES)
            data['asset_env'] = env = ThemeEnvironment(theme_id, data)
            env.register('display_sass', bundle)

            print_stylesheet = data.get('print_stylesheet')
            if print_stylesheet:
                print_bundle = Bundle(bundle, print_stylesheet,
                                      filters=('pyscss', 'indico_cssrewrite', 'csscompressor'),
                                      output="{}_print_%(version)s.css".format(theme_id),
                                      depends=SASS_BASE_MODULES)
                env.register('print_sass', print_bundle)


def register_all_css(env):
    fonts_sass = Bundle('sass/partials/_fonts.scss',
                        filters=('pyscss', 'csscompressor'), output='css/indico_fonts_%(version)s.min.css')

    chartist_css = Bundle('css/lib/chartist.js/chartist.scss',
                          'css/lib/chartist.js/settings/_chartist-settings.scss',
                          filters=('pyscss', 'csscompressor'), output='css/chartist_css_%(version)s.min.css')

    selectize_css = Bundle('css/lib/selectize.js/selectize.css',
                           'css/lib/selectize.js/selectize.default.css',
                           filters='csscompressor', output='css/selectize_css_%(version)s.min.css')

    base_css = Bundle(
        *namespace('css',
                   'Default.css',
                   'timetable.css',
                   'calendar-blue.css',
                   'jquery-ui.css',
                   'lib/angular.css',
                   'lib/jquery.multiselect.css',
                   'lib/jquery.multiselect.filter.css',
                   'lib/jquery.typeahead.css',
                   'lib/fullcalendar.css',
                   'lib/outdatedbrowser.css',
                   'jquery.colorbox.css',
                   'jquery-ui-custom.css',
                   'jquery.colorpicker.css'),
        filters=('csscompressor', 'indico_cssrewrite'),
        output='css/base_%(version)s.min.css')

    conference_css = Bundle('css/Conf_Basic.css',
                            filters=('csscompressor', 'indico_cssrewrite'),
                            output='css/conference_%(version)s.min.css')

    screen_sass = Bundle('sass/screen.scss',
                         filters=('pyscss', 'indico_cssrewrite', 'csscompressor'),
                         output="sass/screen_sass_%(version)s.css",
                         depends=SASS_BASE_MODULES)

    env.register('base_css', base_css)
    env.register('conference_css', conference_css)
    env.register('selectize_css', selectize_css)
    env.register('chartist_css', chartist_css)

    # SASS/SCSS
    env.register('screen_sass', screen_sass)
    env.register('fonts_sass', fonts_sass)

    # Build a bundle with customization CSS if enabled
    custom_css_files = _get_custom_files('scss', '*.scss')
    if custom_css_files:
        env.register('custom_sass', Bundle(*custom_css_files, filters=('pyscss', 'csscompressor'),
                                           output='sass/custom_sass_%(version)s.css'))


core_env = IndicoEnvironment()
