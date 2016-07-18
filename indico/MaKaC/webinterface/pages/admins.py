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

import os
import re
from operator import methodcaller
from urlparse import urljoin

# MaKaC
import MaKaC.common.info as info
import MaKaC.webinterface.pages.conferences as conferences
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.wcomponents as wcomponents
from MaKaC.common.fossilize import fossilize
from MaKaC.webinterface.pages.conferences import WConfModifBadgePDFOptions
from MaKaC.webinterface.pages.main import WPMainBase

# indico
from indico.core.config import Config
from indico.modules import ModuleHolder
from indico.modules.cephalopod import settings as cephalopod_settings
from indico.modules.users import User
from indico.util.i18n import _, get_all_locales
from indico.web.menu import render_sidemenu


class WPAdminsBase(WPMainBase):

    _userData = ['favorite-user-ids']

    def _getSiteArea(self):
        return "AdministrationArea"

    def getCSSFiles(self):
        return WPMainBase.getCSSFiles(self) + self._asset_env['admin_sass'].urls()

    def getJSFiles(self):
        return WPMainBase.getJSFiles(self) + self._includeJSPackage('Management')

    def _getHeader( self ):
        """
        """
        wc = wcomponents.WHeader(self._getAW(), prot_obj=self._protected_object)
        return wc.getHTML( { "subArea": self._getSiteArea(), \
                             "loginURL": self._escapeChars(str(self.getLoginURL())),\
                             "logoutURL": self._escapeChars(str(self.getLogoutURL())), \
                             "tabControl": self._getTabControl() } )

    def _getBody(self, params):
        self._createTabCtrl()
        self._setActiveTab()

        frame = WAdminFrame()

        return frame.getHTML({
            "body": self._getPageContent(params),
            "sideMenu": render_sidemenu('admin-sidemenu', active_item=self.sidemenu_option)
        })

    def _getNavigationDrawer(self):
        return wcomponents.WSimpleNavigationDrawer(_("Server Admin"), urlHandlers.UHAdminArea.getURL, bgColor="white")

    def _createTabCtrl(self):
        pass

    def _getTabContent(self):
        return "nothing"

    def _setActiveTab(self):
        pass

    def _getPageContent(self, params):
        return "nothing"


class WAdmins(wcomponents.WTemplated):

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        wvars['title'] = minfo.getTitle()
        wvars['organisation'] = minfo.getOrganisation()
        wvars['supportEmail'] = Config.getInstance().getSupportEmail()
        wvars['publicSupportEmail'] = Config.getInstance().getPublicSupportEmail()
        wvars['noReplyEmail'] = Config.getInstance().getNoReplyEmail()
        wvars['lang'] = Config.getInstance().getDefaultLocale()
        wvars['address'] = ''
        if minfo.getCity() != '':
            wvars['address'] = minfo.getCity()
        if minfo.getCountry() != '':
            if wvars['address'] != '':
                wvars['address'] = '{0} ({1})'.format(wvars['address'], minfo.getCountry())
            else:
                wvars['address'] = minfo.getCountry()
        wvars['timezone'] = Config.getInstance().getDefaultTimezone()
        wvars['systemIconAdmins'] = Config.getInstance().getSystemIconURL('admin')
        wvars['administrators'] = fossilize(sorted([u.as_avatar for u in User.find(is_admin=True, is_deleted=False)],
                                                   key=methodcaller('getStraightFullName')))
        wvars['tracker_url'] = urljoin(Config.getInstance().getTrackerURL(),
                                       'api/instance/{}'.format(cephalopod_settings.get('uuid')))
        wvars['cephalopod_data'] = {'enabled': cephalopod_settings.get('joined'),
                                    'contact': cephalopod_settings.get('contact_name'),
                                    'email': cephalopod_settings.get('contact_email'),
                                    'url': Config.getInstance().getBaseURL(),
                                    'organisation': minfo.getOrganisation()}
        return wvars


class WAdminFrame(wcomponents.WTemplated):

    def __init__( self ):
        pass

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["imgGestionGrey"] = Config.getInstance().getSystemIconURL( "gestionGrey" )
        vars["titleTabPixels"] = self.getTitleTabPixels()
        vars["intermediateVTabPixels"] = self.getIntermediateVTabPixels()
        return vars

    def getIntermediateVTabPixels( self ):
        return 0

    def getTitleTabPixels( self ):
        return 260



class WPAdmins(WPAdminsBase):
    sidemenu_option = 'general'

    def getJSFiles(self):
        # Cephalopod is needed to check if the data is synced.
        return WPAdminsBase.getJSFiles(self) + self._asset_env['modules_cephalopod_js'].urls()

    def _getPageContent(self, params):
        wc = WAdmins()
        pars = {'GeneralInfoModifURL': urlHandlers.UHGeneralInfoModification.getURL()}
        return wc.getHTML(pars)


class WGeneralInfoModification(wcomponents.WTemplated):

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        genInfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["title"] = genInfo.getTitle()
        vars["organisation"] = genInfo.getOrganisation()
        vars["city"] = genInfo.getCity()
        vars["country"] = genInfo.getCountry()
        vars["language"] = Config.getInstance().getDefaultLocale()
        vars["language_list"] = get_all_locales()
        return vars


class WPGenInfoModification(WPAdmins):

    def _getPageContent(self, params):
        wc = WGeneralInfoModification()
        pars = {"postURL": urlHandlers.UHGeneralInfoPerformModification.getURL()}
        return wc.getHTML(pars)


class WPServicesCommon(WPAdminsBase):
    sidemenu_option = 'ip_acl'

    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()

        self._subTabIPBasedACL = self._tabCtrl.newTab("ip_based_acl", _("IP Based ACL"),
                                                      urlHandlers.UHIPBasedACL.getURL())

    def _getPageContent(self, params):
        return wcomponents.WTabControl(self._tabCtrl, self._getAW()).getHTML(self._getTabContent(params))


class WPTemplatesCommon( WPAdminsBase ):
    sidemenu_option = 'layout'

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()

        self._subTabGeneral = self._tabCtrl.newTab( "general", _("General Definitions"), \
                urlHandlers.UHAdminLayoutGeneral.getURL() )
        self._subTabCSSTpls = self._tabCtrl.newTab( "styles", _("Conference Styles"), \
                urlHandlers.UHAdminsConferenceStyles.getURL() )
        self._subTabBadges = self._tabCtrl.newTab( "badges", _("Badges"), \
                urlHandlers.UHBadgeTemplates.getURL() )
        self._subTabPosters = self._tabCtrl.newTab( "posters", _("Posters"), \
                urlHandlers.UHPosterTemplates.getURL() )

    def _getPageContent(self, params):
        return wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )


class WPBadgeTemplatesBase(WPTemplatesCommon):

    def getCSSFiles(self):
        return WPTemplatesCommon.getCSSFiles(self) + self._asset_env['indico_badges_css'].urls()

    def getJSFiles(self):
        return WPTemplatesCommon.getJSFiles(self) + self._includeJSPackage('badges_js')


class WPAdminLayoutGeneral( WPTemplatesCommon ):

    def _setActiveTab( self ):
        self._subTabGeneral.setActive()

    def __getAvailableTemplates(self):
        tplDir = Config.getInstance().getTPLDir()

        tplRE = re.compile('^([^\.]+)\.([^\.]+)\.tpl$')

        templates = {}

        fnames = os.listdir(tplDir);
        for fname in fnames:
            m = tplRE.match(fname)
            if m:
                templates[m.group(2)] = None

        tplRE = re.compile('^([^\.]+)\.([^\.]+)\.wohl$')

        fnames = os.listdir(os.path.join(tplDir, 'chelp'))
        for fname in fnames:
            m = tplRE.match(fname)
            if m:
                templates[m.group(2)] = None

        cssRE = re.compile('Default.([^\.]+)\.css$')

        fnames = os.listdir(Config.getInstance().getCssDir())
        for fname in fnames:
            m = cssRE.match(fname)
            if m:
                templates[m.group(1)] = None

        return templates.keys()

    def _getTabContent(self, params):
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        socialCfg = minfo.getSocialAppConfig()
        wc = WAdminLayoutGeneral()
        pars = {
            "defaultTemplateSet": minfo.getDefaultTemplateSet(),
            "availableTemplates": self.__getAvailableTemplates(),
            "templateSetFormURL": urlHandlers.UHAdminLayoutSaveTemplateSet.getURL(),
            "socialFormURL": urlHandlers.UHAdminLayoutSaveSocial.getURL(),
            "socialActive": socialCfg.get('active', True),
            "facebookData": socialCfg.get('facebook', {})
        }
        return wc.getHTML(pars)


class WAdminLayoutGeneral(wcomponents.WTemplated):
    pass


class WPAdminsConferenceStyles( WPTemplatesCommon ):

    def _getTabContent( self, params ):
        wp = WAdminsConferenceStyles()
        return wp.getHTML(params)

    def _setActiveTab( self ):
        self._subTabCSSTpls.setActive()


class WAdminsConferenceStyles(wcomponents.WTemplated):

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["contextHelpText"] = _("This is the list of templates that an organizer can use to customize a conference")
        cssTplsModule=ModuleHolder().getById("cssTpls")
        vars["cssTplsModule"] = cssTplsModule
        return vars


class WPBadgeTemplates(WPBadgeTemplatesBase):
    pageURL = "badgeTemplates.py"

    def __init__(self, rh):
        WPBadgeTemplatesBase.__init__(self, rh)

    def _getTabContent( self, params ):
        wp = WBadgeTemplates(info.HelperMaKaCInfo.getMaKaCInfoInstance().getDefaultConference())
        return wp.getHTML(params)

    def _setActiveTab( self ):
        self._subTabBadges.setActive()


class WPPosterTemplates(WPBadgeTemplatesBase):
    pageURL = "posterTemplates.py"

    def __init__(self, rh):
        WPBadgeTemplatesBase.__init__(self, rh)

    def _getTabContent( self, params ):
        wp = WPosterTemplates(info.HelperMaKaCInfo.getMaKaCInfoInstance().getDefaultConference())
        return wp.getHTML(params)

    def _setActiveTab(self):
        self._subTabPosters.setActive()


class WPBadgeTemplateDesign(WPBadgeTemplatesBase):

    def __init__(self, rh, conf, templateId=None, new=False):
        WPBadgeTemplatesBase.__init__(self, rh)
        self._conf = conf
        self.__templateId = templateId
        self.__new = new

    def _setActiveTab(self):
        self._subTabBadges.setActive()

    def _getTabContent(self, params):
        wc = conferences.WConfModifBadgeDesign(self._conf, self.__templateId, self.__new)
        return wc.getHTML()


class WPPosterTemplateDesign(WPBadgeTemplatesBase):

    def __init__(self, rh, conf, templateId=None, new=False):
        WPBadgeTemplatesBase.__init__(self, rh)
        self._conf = conf
        self.__templateId = templateId
        self.__new = new

    def _setActiveTab(self):
        self._subTabPosters.setActive()

    def _getTabContent(self, params):
        wc = conferences.WConfModifPosterDesign(self._conf, self.__templateId, self.__new)
        return wc.getHTML()


class WBadgePosterTemplatingBase(wcomponents.WTemplated):

    DEF_TEMPLATE_BADGE = None

    def __init__(self, conference, user=None):
        wcomponents.WTemplated.__init__(self)
        self._conf = conference
        self._user = user

    def getVars(self):
        uh = urlHandlers
        vars = wcomponents.WTemplated.getVars(self)
        vars['NewDefaultTemplateURL'] = str(self.DEF_TEMPLATE_BADGE.getURL(self._conf,
                                                                             self._conf.getBadgeTemplateManager().getNewTemplateId(), new=True))

        vars['templateList'] = self._getTemplates()
        self._addExtras(vars)

        return vars

    def _getConfTemplates(self):
        """
        To be overridden in inheriting class.
        """
        pass

    def _getTemplates(self):
        templates = []
        rawTemplates = self._getConfTemplates()
        rawTemplates.sort(lambda x, y: cmp(x[1].getName(), y[1].getName()))

        for templateId, template in rawTemplates:
            templates.append(self._processTemplate(templateId, template))

        return templates

    def _addExtras(self, vars):
        """
        To be overridden in inheriting class, adds specific entries
        into the dictionary vars which the child implementation may require.
        """
        pass

    def _processTemplate(self, templateId, template):
        """
        To be overridden in inheriting class, takes the template and its
        ID, the child then processes the data into the format it expects later.
        """
        pass


class WBadgeTemplates(WBadgePosterTemplatingBase):

    DEF_TEMPLATE_BADGE = urlHandlers.UHModifDefTemplateBadge

    def _addExtras(self, vars):
        vars['PDFOptions'] = WConfModifBadgePDFOptions(self._conf,
                                                       showKeepValues=False,
                                                       showTip=False).getHTML()

    def _getConfTemplates(self):
        return self._conf.getBadgeTemplateManager().getTemplates().items()

    def _processTemplate(self, templateId, template):
        uh = urlHandlers

        data = {
            'name': template.getName(),
            'urlEdit': str(uh.UHConfModifBadgeDesign.getURL(self._conf, templateId)),
            'urlDelete': str(uh.UHConfModifBadgePrinting.getURL(self._conf, deleteTemplateId=templateId))
        }

        return data


class WPosterTemplates(WBadgePosterTemplatingBase):

    DEF_TEMPLATE_BADGE = urlHandlers.UHModifDefTemplatePoster

    def _getConfTemplates(self):
        return self._conf.getPosterTemplateManager().getTemplates().items()

    def _processTemplate(self, templateId, template):
        uh = urlHandlers

        data = {
            'name': template.getName(),
            'urlEdit': str(uh.UHConfModifPosterDesign.getURL(self._conf, templateId)),
            'urlDelete': str(uh.UHConfModifPosterPrinting.getURL(self._conf, deleteTemplateId=templateId)),
            'urlCopy': str(uh.UHConfModifPosterPrinting.getURL(self._conf, copyTemplateId=templateId))
        }

        return data


class WPAdminsSystemBase(WPAdminsBase):
    sidemenu_option = 'storage'

    def __init__(self, rh):
        WPAdminsBase.__init__(self, rh)

    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()

        self._subTabConfiguration = self._tabCtrl.newTab("configuration", _("Configuration"),
                                                         urlHandlers.UHAdminsSystem.getURL())
        self._subTabMaintenance = self._tabCtrl.newTab("maintenance", _("Maintenance"),
                                                       urlHandlers.UHMaintenance.getURL())

    def _getPageContent(self, params):
        return wcomponents.WTabControl(self._tabCtrl, self._getAW()).getHTML(self._getTabContent(params))


class WPAdminsSystem(WPAdminsSystemBase):

    def _setActiveTab(self):
        self._subTabConfiguration.setActive()

    def _getTabContent(self, params):
        wc = WAdminsSystem()
        return wc.getHTML(params)


class WAdminsSystem(wcomponents.WTemplated):

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["minfo"] = minfo
        vars["ModifURL"] = urlHandlers.UHAdminsSystemModif.getURL()
        vars['use_proxy'] = Config.getInstance().getUseProxy()
        return vars


class WPAdminsSystemModif(WPAdminsSystemBase):

    def _getTabContent(self, params):
        wc = WAdminsSystemModif()
        return wc.getHTML(params)


class WAdminsSystemModif(wcomponents.WTemplated):

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["minfo"] = minfo
        vars["postURL"] = urlHandlers.UHAdminsSystemModif.getURL()
        return vars


class WPMaintenanceBase(WPAdminsSystemBase):

    def __init__(self, rh):
        WPAdminsBase.__init__(self, rh)

    def _setActiveTab(self):
        self._subTabMaintenance.setActive()


class WPMaintenance(WPMaintenanceBase):

    def __init__(self, rh, s, dbSize):
        WPMaintenanceBase.__init__(self, rh)
        self._stat = s
        self._dbSize = dbSize

    def _getTabContent(self, params):
        wc = WAdminMaintenance()
        pars = { "cleanupURL": urlHandlers.UHMaintenanceTmpCleanup.getURL(), \
                 "tempSize": self._stat[0], \
                 "nFiles": "%s files" % self._stat[1], \
                 "nDirs": "%s folders" % self._stat[2], \
                 "packURL": urlHandlers.UHMaintenancePack.getURL(), \
                 "dbSize": self._dbSize}
        return wc.getHTML(pars)


class WAdminMaintenance(wcomponents.WTemplated):

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        return vars


class WPMaintenanceTmpCleanup(WPMaintenanceBase):

    def __init__(self, rh):
        WPMaintenanceBase.__init__(self, rh)

    def _getTabContent(self, params):
        msg = """Are you sure you want to delete the temporary directory
        (note that all the files in that directory will be deleted)?"""
        wc = wcomponents.WConfirmation()
        url = urlHandlers.UHMaintenancePerformTmpCleanup.getURL()
        return """
                <table align="center" width="95%%">
                    <tr>
                        <td class="formTitle">Maintenance: Cleaning-up temporary directory</td>
                    </tr>
                    <tr>
                        <td>
                    <br>
                            %s
                        </td>
                    </tr>
                </table>
                """ % wc.getHTML(msg, url, {})


class WPMaintenancePack(WPMaintenanceBase):

    def __init__(self, rh):
        WPMaintenanceBase.__init__(self, rh)

    def _getTabContent(self, params):
        wc = wcomponents.WConfirmation()
        msg = """Are you sure you want to pack the database?"""
        url = urlHandlers.UHMaintenancePerformPack.getURL()
        return """
                <table align="center" width="95%%">
                    <tr>
                        <td class="formTitle">Maintenance: Database packing</td>
                    </tr>
                    <tr>
                        <td>
                    <br>
                            %s
                        </td>
                    </tr>
                </table>
                """ % wc.getHTML(msg, url, {})


class WPIPBasedACL( WPServicesCommon ):

    def __init__( self, rh ):
        WPServicesCommon.__init__( self, rh )

    def _getTabContent(self, params):
        wc = WIPBasedACL()
        return wc.getHTML(params)

    def _setActiveTab(self):
        self._subTabIPBasedACL.setActive()


class WIPBasedACL(wcomponents.WTemplated):

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["ipList"] = minfo.getIPBasedACLMgr().get_full_access_acl()
        vars["removeIcon"] = Config.getInstance().getSystemIconURL("remove")
        return vars
