<% from MaKaC.webinterface.materialFactories import MaterialFactoryRegistry %>
<% from MaKaC.common import Config %>
<% from MaKaC.authentication.AuthenticationMgr import AuthenticatorMgr %>
<% import MaKaC.common.info as info %>
<% from MaKaC.rb_location import Location %>
<% import simplejson %>
<% import MaKaC.webinterface.common.tools as securityTools %>
<%
config = Config.getInstance()
authenticators = filter(lambda x: x.id != 'Local', AuthenticatorMgr().getList())
extAuths = list((auth.id, auth.name) for auth in authenticators)

rbActive = info.HelperMaKaCInfo.getMaKaCInfoInstance().getRoomBookingModuleActive()
if rbActive:
    locationList = {}
    locationNames = map(lambda l: l.friendlyName, Location.allLocations)

    for name in locationNames:
        locationList[name] = name;
else:
    locationList = None

if Location.getDefaultLocation():
    defaultLocation = Location.getDefaultLocation().friendlyName
else:
    defaultLocation = ""
%>

var Indico = {
    SystemIcons: {
        conference: "${ iconFileName("conference") }",
        lecture: "${ iconFileName("lecture") }",
        meeting: "${ iconFileName("meeting") }",
        help: "${ iconFileName("help") }",
        arrow_previous: "${ iconFileName("arrow_previous") }",
        arrow_next: "${ iconFileName("arrow_next") }",
        dot_gray: "${ iconFileName("dot_gray") }",
        dot_blue: "${ iconFileName("dot_blue") }",
        dot_green: "${ iconFileName("dot_green") }",
        dot_red: "${ iconFileName("dot_red") }",
        dot_orange: "${ iconFileName("dot_orange") }",
        loading: "${ iconFileName("loading") }",
        ui_loading: "${ iconFileName("ui_loading") }",
        role_participant: "${ iconFileName("role_participant") }",
        role_creator: "${ iconFileName("role_creator") }",
        role_manager: "${ iconFileName("role_manager") }",
        remove: "${ iconFileName("remove") }",
        remove_faded: "${ iconFileName("remove_faded") }",
        add: "${ iconFileName("add") }",
        add_faded: "${ iconFileName("add_faded") }",
        basket: "${ iconFileName("basket") }",
        tick: "${ iconFileName("tick") }",
        edit: "${ iconFileName("edit") }",
        edit_faded: "${ iconFileName("edit_faded") }",
        currentMenuItem: "${ iconFileName("currentMenuItem") }",
        itemExploded:"${ iconFileName("itemExploded") }",
        enabledSection: "${ iconFileName("enabledSection") }",
        disabledSection: "${ iconFileName("disabledSection") }",
        timezone: "${ iconFileName("timezone") }",
        basket: "${ iconFileName("basket") }",
        play: "${ iconFileName("play") }",
        stop: "${ iconFileName("stop") }",
        play_small: "${ iconFileName("play_small") }",
        stop_small: "${ iconFileName("stop_small") }",
        reload: "${ iconFileName("reload") }",
        reload_faded: "${ iconFileName("reload_faded") }",
        mail_big: "${ iconFileName("mail_big") }",
        play_faded: "${ iconFileName("play_faded") }",
        stop_faded: "${ iconFileName("stop_faded") }",
        play_faded_small: "${ iconFileName("play_faded_small") }",
        stop_faded_small: "${ iconFileName("stop_faded_small") }",
        info: "${ iconFileName("info") }",
        accept: "${ iconFileName("accept") }",
        reject:"${ iconFileName("reject") }",
        user:"${ iconFileName("user") }",
        room:"${ iconFileName("room") }",
        popupMenu: "${ iconFileName("popupMenu")}",
        roomwidgetArrow: "${ iconFileName("roomwidgetArrow")}",
        breadcrumbArrow: "${ iconFileName("breadcrumbArrow")}",
        star: "${ iconFileName("star")}",
        starGrey: "${ iconFileName("starGrey")}",
        warning_yellow: "${ iconFileName("warning_yellow")}",
        arrow_up: "${ iconFileName("upArrow")}",
        arrow_down: "${ iconFileName("downArrow")}",
        indico_small: "${ iconFileName("indico_small")}",
        protected: "${ iconFileName("protected")}",
        calendarWidget: "${ iconFileName("calendarWidget") }"
    },
    FileTypeIcons:
        ${ simplejson.dumps(dict((k.lower(),v[2]) for k,v in config.getFileTypes().iteritems())) }
    ,
    Urls: {
        JsonRpcService: window.location.protocol == "https:"?"${ urlHandlers.UHJsonRpcService.getURL(secure=True) }":"${ urlHandlers.UHJsonRpcService.getURL() }",

        ImagesBase: "${ Config.getInstance().getImagesBaseURL() }",
        SecureImagesBase: "${ Config.getInstance().getImagesBaseSecureURL() }",

        Login: "${ urlHandlers.UHSignIn.getURL() }",

        Favourites: "${ urlHandlers.UHUserBaskets.getURL() }",

        ConferenceDisplay: "${ urlHandlers.UHConferenceDisplay.getURL() }",
        ContributionDisplay: "${ urlHandlers.UHContributionDisplay.getURL() }",
        SessionDisplay: "${ urlHandlers.UHSessionDisplay.getURL() }",
        ConfCollaborationDisplay: "${ urlHandlers.UHCollaborationDisplay.getURL() }",

        ContribToXML: "${ urlHandlers.UHContribToXML.getURL() }",
        ContribToPDF: "${ urlHandlers.UHContribToPDF.getURL() }",
        ContribToiCal: "${ urlHandlers.UHContribToiCal.getURL() }",

        SessionToiCal:  "${ urlHandlers.UHSessionToiCal.getURL() }",
        ConfTimeTablePDF: "${ urlHandlers.UHConfTimeTablePDF.getURL() }",
        ConfTimeTableCustomPDF: "${ urlHandlers.UHConfTimeTableCustomizePDF.getURL() }",

        SessionModification: "${ urlHandlers.UHSessionModification.getURL() }",
        ContributionModification: "${ urlHandlers.UHContributionModification.getURL() }",
        BreakModification: "${ urlHandlers.UHConfModifyBreak.getURL() }",

        Reschedule: "${ urlHandlers.UHConfModifReschedule.getURL() }",
        SlotCalc: "${ urlHandlers.UHSessionModSlotCalc.getURL() }",
        FitSessionSlot: "${ urlHandlers.UHSessionFitSlot.getURL() }",

        UploadAction: {
            subcontribution: '${ str(urlHandlers.UHSubContribModifAddMaterials.getURL()) }',
            contribution: '${ str(urlHandlers.UHContribModifAddMaterials.getURL()) }',
            session: '${ str(urlHandlers.UHSessionModifAddMaterials.getURL()) }',
            conference: '${ str(urlHandlers.UHConfModifAddMaterials.getURL()) }',
            category: '${ str(urlHandlers.UHCategoryAddMaterial.getURL()) }'
        },

        RoomBookingForm: "${ urlHandlers.UHRoomBookingBookingForm.getURL() }",
        RoomBookingDetails: "${ urlHandlers.UHRoomBookingRoomDetails.getURL() }",
        ConfModifSchedule: "${ urlHandlers.UHConfModifSchedule.getURL() }",
        SubcontrModif: "${ urlHandlers.UHContribModifSubCont.getURL() }"
    },

    Data: {
        MaterialTypes: { meeting : ${ simplejson.dumps(list((k,k.title()) for k in MaterialFactoryRegistry._allowedMaterials['meeting'])) },
        simple_event: ${ simplejson.dumps(list((k,k.title()) for k in MaterialFactoryRegistry._allowedMaterials['simple_event'])) },
        conference: ${ simplejson.dumps(list((k,k.title()) for k in MaterialFactoryRegistry._allowedMaterials['conference'])) },
        category: ${ simplejson.dumps(list((k,k.title()) for k in MaterialFactoryRegistry._allowedMaterials['category'])) }},
        WeekDays: ${ [ "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday" ] },
        DefaultLocation: '${ str(defaultLocation) }',
        Locations: ${ jsonEncode(locationList) }
    },

    Security:{
        allowedTags: "${ ",".join(securityTools.allowedTags) }",
        allowedAttributes: "${ ",".join(securityTools.allowedAttrs) }",
        allowedCssProperties: "${ ",".join(securityTools.allowedCssProperties) }",
        allowedProtocols: "${ ",".join(securityTools.allowedProtocols) }",
        urlProperties: "${ ",".join(securityTools.urlProperties) }",
        sanitizationLevel: ${ Config.getInstance().getSanitizationLevel() }
    },

    Settings: {
        ExtAuthenticators: ${ jsonEncode(extAuths) },
        RoomBookingModuleActive: ${ jsBoolean(rbActive) }
    },

    FileRestrictions: {
        MaxUploadFilesTotalSize: ${ config.getMaxUploadFilesTotalSize() },
        MaxUploadFileSize: ${ config.getMaxUploadFileSize() }
    }
};
