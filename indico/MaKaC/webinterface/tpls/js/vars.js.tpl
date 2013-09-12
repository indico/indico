<% from MaKaC.webinterface.materialFactories import MaterialFactoryRegistry %>
<% from MaKaC.common import Config %>
<% from MaKaC.authentication.AuthenticationMgr import AuthenticatorMgr %>
<% import MaKaC.common.info as info %>
<% from MaKaC.rb_location import Location %>
<% from indico.util import json %>
<% import MaKaC.webinterface.common.tools as securityTools %>
<% from MaKaC.export import fileConverter %>
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

    if Location.getDefaultLocation():
        defaultLocation = Location.getDefaultLocation().friendlyName
    else:
        defaultLocation = ""
else:
    locationList = None
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
        reload: "${ iconFileName("reload") }",
        reload_faded: "${ iconFileName("reload_faded") }",
        mail_big: "${ iconFileName("mail_big") }",
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
        calendarWidget: "${ iconFileName("calendarWidget") }",
        tt_time: "${ iconFileName("tt_time") }"
    },
    FileTypeIcons:
        ${ json.dumps(dict((k.lower(),v[2]) for k,v in config.getFileTypes().iteritems())) }
    ,
    Urls: {
        JsonRpcService: window.location.protocol == "https:"?"${ urlHandlers.UHJsonRpcService.getURL(secure=True) }":"${ urlHandlers.UHJsonRpcService.getURL() }",

        Base: (window.location.protocol == "https:" ? "${ Config.getInstance().getBaseSecureURL() }" : "${ Config.getInstance().getBaseURL() }"),

        ImagesBase: "${ Config.getInstance().getImagesBaseURL() }",
        SecureImagesBase: "${ Config.getInstance().getImagesBaseSecureURL() }",

        ExportAPIBase: (window.location.protocol == "https:" ? "${ urlHandlers.UHAPIExport.getURL(secure=True) }" : "${ urlHandlers.UHAPIExport.getURL() }"),
        APIBase: (window.location.protocol == "https:" ? "${ urlHandlers.UHAPIAPI.getURL(secure=True) }" : "${ urlHandlers.UHAPIAPI.getURL() }"),

        Login: ${ urlHandlers.UHSignIn.getURL().js_router | j,n },
        Favourites: ${ urlHandlers.UHUserBaskets.getURL(_ignore_static=True).js_router | j,n },

        ConferenceDisplay: ${ urlHandlers.UHConferenceDisplay.getURL(_ignore_static=True).js_router | j,n },
        ContributionDisplay: ${ urlHandlers.UHContributionDisplay.getURL(_ignore_static=True).js_router | j,n },
        SessionDisplay: ${ urlHandlers.UHSessionDisplay.getURL(_ignore_static=True).js_router | j,n },

        ContribToXML: ${ urlHandlers.UHContribToXML.getURL(_ignore_static=True).js_router | j,n },
        ContribToPDF: ${ urlHandlers.UHContribToPDF.getURL(_ignore_static=True).js_router | j,n },

        ConfTimeTablePDF: ${ urlHandlers.UHConfTimeTablePDF.getURL(_ignore_static=True).js_router | j,n },
        ConfTimeTableCustomPDF: ${ urlHandlers.UHConfTimeTableCustomizePDF.getURL(_ignore_static=True).js_router | j,n },

        SessionModification: ${ urlHandlers.UHSessionModification.getURL(_ignore_static=True).js_router | j,n },
        ContributionModification: ${ urlHandlers.UHContributionModification.getURL(_ignore_static=True).js_router | j,n },
        SessionProtection: ${ urlHandlers.UHSessionModifAC.getURL(_ignore_static=True).js_router | j,n },
        ContributionProtection: ${ urlHandlers.UHContribModifAC.getURL(_ignore_static=True).js_router | j,n },

        Reschedule: ${ urlHandlers.UHConfModifReschedule.getURL(_ignore_static=True).js_router | j,n },
        SlotCalc: ${ urlHandlers.UHSessionModSlotCalc.getURL(_ignore_static=True).js_router | j,n },
        FitSessionSlot: ${ urlHandlers.UHSessionFitSlot.getURL(_ignore_static=True).js_router | j,n },

        UploadAction: {
            subcontribution: ${ urlHandlers.UHSubContribModifAddMaterials.getURL(_ignore_static=True).js_router | j,n },
            contribution: ${ urlHandlers.UHContribModifAddMaterials.getURL(_ignore_static=True).js_router | j,n },
            session: ${ urlHandlers.UHSessionModifAddMaterials.getURL(_ignore_static=True).js_router | j,n },
            conference: ${ urlHandlers.UHConfModifAddMaterials.getURL(_ignore_static=True).js_router | j,n },
            category: ${ urlHandlers.UHCategoryAddMaterial.getURL(_ignore_static=True).js_router | j,n }
        },

        RoomBookingBookRoom: ${ urlHandlers.UHRoomBookingBookRoom.getURL(_ignore_static=True).js_router | j,n },
        RoomBookingForm: ${ urlHandlers.UHRoomBookingBookingForm.getURL(_ignore_static=True).js_router | j,n },
        RoomBookingDetails: ${ urlHandlers.UHRoomBookingRoomDetails.getURL(_ignore_static=True).js_router | j,n },
        ConfModifSchedule: ${ urlHandlers.UHConfModifSchedule.getURL(_ignore_static=True).js_router | j,n },
        SubcontrModif: ${ urlHandlers.UHContribModifSubCont.getURL(_ignore_static=True).js_router | j,n },
        AuthorDisplay: ${ urlHandlers.UHContribAuthorDisplay.getURL(_ignore_static=True).js_router | j,n },
        AuthorEmail: ${ urlHandlers.UHConferenceEmail.getURL(_ignore_static=True).js_router | j,n }
    },

    Data: {
        MaterialTypes: { meeting : ${ json.dumps(list((k,k.title()) for k in MaterialFactoryRegistry._allowedMaterials['meeting'])) },
        simple_event: ${ json.dumps(list((k,k.title()) for k in MaterialFactoryRegistry._allowedMaterials['simple_event'])) },
        conference: ${ json.dumps(list((k,k.title()) for k in MaterialFactoryRegistry._allowedMaterials['conference'])) },
        category: ${ json.dumps(list((k,k.title()) for k in MaterialFactoryRegistry._allowedMaterials['category'])) }},
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
    },

    PDFConversion: {
        AvailablePDFConversions: ${fileConverter.CDSConvFileConverter.getAvailableConversions()},
        HasFileConverter: ${jsonEncode(Config.getInstance().hasFileConverter())}
    }

};
