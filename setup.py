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


import ast
import os
import re
from distutils.command.build import build
from setuptools import setup, find_packages


ENTRY_POINTS = {
    'console_scripts': [
        'indico = indico.cli.core:cli',
        'indico-setup = indico.cli.setup:cli',
        'indico-zodbimport = indico_zodbimport.cli:main',
    ],
    'pytest11': [
        'indico = indico.testing.pytest_plugin',
    ],
    'indico.zodb_importers': [
        'roombooking = indico_zodbimport.modules.roombooking:RoomBookingImporter',
        'payment = indico_zodbimport.modules.payment:PaymentImporter',
        'api = indico_zodbimport.modules.api:APIImporter',
        'users = indico_zodbimport.modules.users:UserImporter',
        'groups = indico_zodbimport.modules.groups:GroupImporter',
        'static_sites = indico_zodbimport.modules.static_sites:StaticSitesImporter',
        'event_alarms = indico_zodbimport.modules.event_alarms:EventAlarmImporter',
        'legacy_events = indico_zodbimport.modules.legacy_events:LegacyEventImporter',
        'legacy_categories = indico_zodbimport.modules.legacy_categories:LegacyCategoryImporter',
        'event_logs = indico_zodbimport.modules.event_logs:EventLogImporter',
        'event_notes = indico_zodbimport.modules.event_notes:EventNoteImporter',
        'attachments = indico_zodbimport.modules.attachments:AttachmentImporter',
        'event_images = indico_zodbimport.modules.event_images:EventImageImporter',
        'event_stubs = indico_zodbimport.modules.event_stubs:EventStubImporter',
        'event_menus = indico_zodbimport.modules.event_menus:EventMenuImporter',
        'event_layout = indico_zodbimport.modules.event_layout:EventLayoutImporter',
        'event_surveys = indico_zodbimport.modules.event_surveys:SurveyImporter',
        'event_managers = indico_zodbimport.modules.event_managers:EventManagerImporter',
        'event_regforms = indico_zodbimport.modules.event_regforms:EventRegformImporter',
        'event_participants = indico_zodbimport.modules.event_participants:EventParticipantsImporter',
        'event_timetable = indico_zodbimport.modules.event_timetable:EventTimetableImporter',
        'event_locations = indico_zodbimport.modules.event_locations:EventLocationsImporter',
        'event_categories = indico_zodbimport.modules.event_categories:EventCategoriesImporter',
        'event_dates_titles = indico_zodbimport.modules.event_dates_titles:EventDatesTitlesImporter',
        'event_abstracts_zodb = indico_zodbimport.modules.event_abstracts_zodb:EventAbstractZODBPatcher',
        'event_paper_reviewing_legacy = indico_zodbimport.modules.event_paper_reviewing_legacy:LegacyEventPaperReviewingImporter',
        'legal = indico_zodbimport.modules.legal:LegalImporter',
        'networks = indico_zodbimport.modules.networks:NetworkImporter',
        'categories = indico_zodbimport.modules.categories:CategoryImporter',
        'event_acls = indico_zodbimport.modules.event_acls:EventACLImporter',
        'upcoming_events = indico_zodbimport.modules.upcoming_events:UpcomingEventsImporter',
        'news = indico_zodbimport.modules.news:NewsImporter',
        'event_types = indico_zodbimport.modules.event_types:EventTypeImporter',
        'user_management = indico_zodbimport.modules.user_management:UserManagementImporter',
        'event_series = indico_zodbimport.modules.event_series:EventSeriesImporter',
        'event_keywords_ctimes_visibility = indico_zodbimport.modules.event_keywords_ctimes_visibility:EventKeywordsCreationTimesVisibilityImporter',
        'event_abstracts = indico_zodbimport.modules.event_abstracts:EventAbstractsImporter',
        'event_papers = indico_zodbimport.modules.event_papers:EventPapersImporter',
        'event_shorturls = indico_zodbimport.modules.event_shorturls:EventShorturlsImporter',
        'global_ip_acl = indico_zodbimport.modules.global_ip_acl:GlobalIPACLImporter',
        'global_settings = indico_zodbimport.modules.global_settings:GlobalSettingsImporter',
        'badges_posters = indico_zodbimport.modules.badges_posters:BadgePosterImporter',
        'event_data = indico_zodbimport.modules.event_data:EventDataImporter',
    ]
}


def read_requirements_file(fname):
    with open(fname, 'r') as f:
        return [dep.strip() for dep in f.readlines() if not (dep.startswith('-') or '://' in dep)]


def get_requirements():
    return read_requirements_file(os.path.join(os.path.dirname(__file__), 'requirements.txt'))


def get_version():
    _version_re = re.compile(r'__version__\s+=\s+(.*)')
    with open('indico/__init__.py', 'rb') as f:
        return str(ast.literal_eval(_version_re.search(f.read().decode('utf-8')).group(1)))


class BuildWithTranslations(build):
    def _compile_languages(self):
        from babel.messages import frontend
        compile_cmd = frontend.compile_catalog(self.distribution)
        self.distribution._set_command_options(compile_cmd)
        compile_cmd.finalize_options()
        compile_cmd.run()

    def run(self):
        self._compile_languages()
        build.run(self)


if __name__ == '__main__':
    setup(
        name='indico',
        version=get_version(),
        cmdclass={'build': BuildWithTranslations},
        description='Indico is a full-featured conference lifecycle management and meeting/lecture scheduling tool',
        author='Indico Team',
        author_email='indico-team@cern.ch',
        url='http://indico-software.org',
        download_url='https://github.com/indico/indico/releases',
        long_description="Indico allows you to schedule conferences, from single talks to complex meetings with "
                         "sessions and contributions. It also includes an advanced user delegation mechanism, "
                         "allows paper reviewing, archival of conference information and electronic proceedings",
        license='https://www.gnu.org/licenses/gpl-3.0.txt',
        zip_safe=False,
        packages=find_packages(),
        include_package_data=True,
        install_requires=get_requirements(),
        entry_points=ENTRY_POINTS)
