# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN)
##
## Indico is free software: you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico.  If not, see <http://www.gnu.org/licenses/>.


"""
This file declares all core JS/CSS assets used by Indico
"""
# stdlib imports
import os

# 3rd party libs
from webassets import Bundle, Environment
from webassets.filter import Filter

# legacy imports
from MaKaC.common import HelperMaKaCInfo
from MaKaC.common.Configuration import Config


class PluginEnvironment(Environment):
    def __init__(self, plugin_name, plugin_dir, url_path):
        config = Config.getInstance()
        output_dir = os.path.join(config.getHtdocsDir(), 'build', plugin_name)

        super(PluginEnvironment, self).__init__(output_dir, url_path)

        self.append_path(os.path.join(plugin_dir, 'htdocs'), url=url_path)


def namespace(dir_ns, *list_files):
    return [os.path.join(dir_ns, f) for f in list_files]


indico_core = Bundle(
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
               'Widgets/DateTime.js',
               'Widgets/Menu.js',
               'Widgets/RichText.js',
               'Widgets/Navigation.js',
               'Widgets/UserList.js',
               'Dialogs/Popup.js',
               'Dialogs/PopupWidgets.js',
               'Dialogs/Base.js',
               'Dialogs/Util.js',
               'Dialogs/Users.js',
               'Dialogs/PopupWidgets.js',
               'Browser.js',
               'Services.js',
               'Util.js',
               'Login.js',
               'Dragndrop.js'),
    filters='rjsmin', output='js/indico_core_%(version)s.min.js')

indico_management = Bundle(
    *namespace('js/indico/Management',

               'ConfModifDisplay.js',
               'RoomBooking.js',
               'eventCreation.js',
               'Timetable.js',
               'AbstractReviewing.js',
               'NotificationTPL.js',
               'Registration.js',
               'Contributions.js',
               'Sessions.js',
               'CFA.js',
               'RoomBookingMapOfRooms.js',
               'EventUsers.js'),
    filters='rjsmin', output='js/indico_management_%(version)s.min.js')

indico_room_booking = Bundle(
    'js/indico/jquery/multiselect.js',
    *namespace('js/indico/RoomBooking',

               'MapOfRooms.js',
               'BookingForm.js',
               'RoomBookingCalendar.js'),
    filters='rjsmin', output='js/indico_room_booking_%(version)s.min.js')

indico_admin = Bundle(
    *namespace('js/indico/Admin',

               'News.js',
               'Scheduler.js',
               'Upcoming.js'),
    filters='rjsmin', output='js/indico_admin_%(version)s.min.js')

indico_timetable = Bundle(
    *namespace('js/indico/Timetable',

               'Filter.js',
               'Layout.js',
               'Undo.js',
               'Base.js',
               'DragAndDrop.js',
               'Draw.js',
               'Management.js'),
    filters='rjsmin', output='js/indico_timetable_%(version)s.min.js')

indico_legacy = Bundle(
    *namespace('js/indico/Legacy',

               'Widgets.js',
               'Dialogs.js',
               'Util.js'),
    filters='rjsmin', output='js/indico_legacy_%(version)s.min.js')

indico_common = Bundle(
    *namespace('js/indico/Common',
               'Export.js',
               'TimezoneSelector.js',
               'Social.js',
               'htmlparser.js'),
    filters='rjsmin', output='js/indico_common_%(version)s.min.js')

indico_materialeditor = Bundle('js/indico/MaterialEditor/Editor.js',
                               filters='rjsmin', output='js/indico_materialeditor_%(version)s.min.js')

indico_display = Bundle('js/indico/Display/Dialogs.js',
                        filters='rjsmin', output='js/indico_display_%(version)s.min.js')

indico_jquery = Bundle(
    *namespace('js/indico/jquery',

               'defaults.js',
               'global.js',
               'multiselect.js'),
    filters='rjsmin', output='js/indico_jquery_%(version)s.min.js')

indico_jquery_authors = Bundle('js/indico/jquery/authors.js',
                               filters='rjsmin', output='js/indico_jquery_authors_%(version)s.min.js')

indico_badges_js = Bundle('js/indico/Management/ConfModifBadgePosterPrinting.js',
                          filters='jsmin', output='js/indico_badges_%(version)s.min.js')

indico_badges_css = Bundle('css/badges.css',
                           filters='cssmin', output='css/indico_badges_%(version)s.min.css')


class DebugLevelFilter(Filter):
    name = 'debug_level'
    max_debug_level = None

    def __init__(self, required_level):
        super(DebugLevelFilter, self).__init__()
        self.required_level = required_level

    def unique(self):
        # We cannot have self.env available here so we take the debug flag from makacinfo instead.
        debug = HelperMaKaCInfo.getMaKaCInfoInstance().isDebugActive()
        return self.name, self.required_level, debug

    def output(self, in_, out, **kw):
        if self.required_level == self.env.debug:
            out.write(in_.read())


jquery = Bundle(
    'js/lib/underscore.js',
    'js/lib/jquery.js',
    'js/lib/jquery.qtip.js',
    Bundle('js/jquery/jquery-migrate-silencer.js', filters=DebugLevelFilter(required_level=False),
           output='js/jquery_migrate_silencer_%(version)s.js'),
    *namespace('js/jquery',

        'jquery-migrate.js',
        'jquery-ui.js',
        'jquery.form.js',
        'jquery.custom.js',
        'jquery.daterange.js',
        'jquery.form.js',
        'jquery.dttbutton.js',
        'jquery.colorbox.js',
        'jquery.menu.js',
        'date.js',
        'jquery.multiselect.js',
        'jquery.colorpicker.js',
        'jquery-extra-selectors.js',
        'jquery.typewatch.js',
        'jquery.multiselect.filter.js',
        'jstorage.js',
        'jquery.watermark.js'),
    filters='rjsmin', output='js/jquery_code_%(version)s.min.js')

presentation = Bundle(
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
        'Data/Watch.js',
        'Data/WatchValue.js',
        'Data/WatchList.js',
        'Data/WatchObject.js',
        'Data/Binding.js',
        'Data/Logic.js',
        'Data/Json.js',
        'Data/Remote.js',
        'Data/DateTime.js',
        'Ui/MimeTypes.js',
        'Ui/XElement.js',
        'Ui/Html.js',
        'Ui/Dom.js',
        'Ui/Style.js',
        'Ui/Extensions/Lookup.js',
        'Ui/Extensions/Layout.js',
        'Ui/Text.js',
        'Ui/Styles/SimpleStyles.js',
        'Ui/Widgets/WidgetBase.js',
        'Ui/Widgets/WidgetPage.js',
        'Ui/Widgets/WidgetComponents.js',
        'Ui/Widgets/WidgetControl.js',
        'Ui/Widgets/WidgetEditor.js',
        'Ui/Widgets/WidgetTable.js',
        'Ui/Widgets/WidgetField.js',
        'Ui/Widgets/WidgetEditable.js',
        'Ui/Widgets/WidgetMenu.js',
        'Ui/Widgets/WidgetGrid.js'),
    filters='rjsmin', output='presentation_%(version)s.min.js')

ie_compatibility = Bundle('js/selectivizr.js',
                          filters='rjsmin', output='js/ie_compatibility_%(version)s.min.js')

moment = Bundle(
    *namespace('js/moment',
        'moment.js',
        'lang/es.js',
        'lang/fr.js'),
    filters='rjsmin', output='js/moment_%(version)s.min.js')

base_js = Bundle(jquery, presentation, indico_jquery, moment, indico_core,
                 indico_legacy, indico_common)

base_sass = Bundle('sass/screen.scss',
                   filters=("pyscss", "cssrewrite", "cssmin"),
                   output="sass/screen_sass_%(version)s.css",
                   depends=["sass/base/*.scss",
                            "sass/partials/*.scss"])


def register_all_js(env):
    env.register('jquery', jquery)
    env.register('presentation', presentation)
    env.register('indico_core', indico_core)
    env.register('indico_management', indico_management)
    env.register('indico_roombooking', indico_room_booking)
    env.register('indico_admin', indico_admin)
    env.register('indico_timetable', indico_timetable)
    env.register('indico_legacy', indico_legacy)
    env.register('indico_common', indico_common)
    env.register('indico_materialeditor', indico_materialeditor)
    env.register('indico_display', indico_display)
    env.register('indico_jquery', indico_jquery)
    env.register('indico_authors', indico_jquery_authors)
    env.register('indico_badges_js', indico_badges_js)
    env.register('base_js', base_js)
    env.register('ie_compatibility', ie_compatibility)


def register_all_css(env, main_css_file):

    base_css = Bundle(
        *namespace('css',
                   main_css_file,
                    'category_display.css',
                    'calendar-blue.css',
                    'jquery-ui.css',
                    'lib/jquery.qtip.css',
                    'jquery.colorbox.css',
                    'jquery-ui-custom.css',
                    'jquery.qtip-custom.css',
                    'jquery.colorpicker.css',
                    'jquery.multiselect.filter.css',
                    'jquery.multiselect.css'),
        filters=("cssmin", "cssrewrite"),
        output='css/base_%(version)s.min.css')

    env.register('indico_badges_css', indico_badges_css)
    env.register('base_css', base_css)
    env.register('base_sass', base_sass)
