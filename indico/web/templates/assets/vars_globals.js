var Indico = {
    FileTypeIcons:
        {{ file_type_icons | tojson }},
    Urls: {
        JsonRpcService: window.location.protocol == "https:"?"{{ urls.UHJsonRpcService.getURL(secure=True) }}":"{{ urls.UHJsonRpcService.getURL() }}",

        Base: (window.location.protocol == "https:" ? "{{ config.getBaseSecureURL() }}" : "{{ config.getBaseURL() }}"),

        ImagesBase: "{{ config.getImagesBaseURL() }}",
        SecureImagesBase: "{{ config.getImagesBaseSecureURL() }}",

        ExportAPIBase: (window.location.protocol == "https:" ? "{{ urls.UHAPIExport.getURL(secure=True) }}" : "{{ urls.UHAPIExport.getURL() }}"),
        APIBase: (window.location.protocol == "https:" ? "{{ urls.UHAPIAPI.getURL(secure=True) }}" : "{{ urls.UHAPIAPI.getURL() }}"),

        Login: {{ urls.UHSignIn.getURL().js_router | tojson }},
        Favourites: {{ urls.UHUserBaskets.getURL(_ignore_static=True).js_router | tojson }},

        ConferenceDisplay: {{ urls.UHConferenceDisplay.getURL(_ignore_static=True).js_router | tojson }},
        ContributionDisplay: {{ urls.UHContributionDisplay.getURL(_ignore_static=True).js_router | tojson }},
        SessionDisplay: {{ urls.UHSessionDisplay.getURL(_ignore_static=True).js_router | tojson }},

        ContribToXML: {{ urls.UHContribToXML.getURL(_ignore_static=True).js_router | tojson }},
        ContribToPDF: {{ urls.UHContribToPDF.getURL(_ignore_static=True).js_router | tojson }},

        ConfTimeTablePDF: {{ urls.UHConfTimeTablePDF.getURL(_ignore_static=True).js_router | tojson }},
        ConfTimeTableCustomPDF: {{ urls.UHConfTimeTableCustomizePDF.getURL(_ignore_static=True).js_router | tojson }},

        SessionModification: {{ urls.UHSessionModification.getURL(_ignore_static=True).js_router | tojson }},
        ContributionModification: {{ urls.UHContributionModification.getURL(_ignore_static=True).js_router | tojson }},
        SessionProtection: {{ urls.UHSessionModifAC.getURL(_ignore_static=True).js_router | tojson }},
        ContributionProtection: {{ urls.UHContribModifAC.getURL(_ignore_static=True).js_router | tojson }},

        Reschedule: {{ urls.UHConfModifReschedule.getURL(_ignore_static=True).js_router | tojson }},
        SlotCalc: {{ urls.UHSessionModSlotCalc.getURL(_ignore_static=True).js_router | tojson }},
        FitSessionSlot: {{ urls.UHSessionFitSlot.getURL(_ignore_static=True).js_router | tojson }},

        UploadAction: {
            subcontribution: {{ urls.UHSubContribModifAddMaterials.getURL(_ignore_static=True).js_router | tojson }},
            contribution: {{ urls.UHContribModifAddMaterials.getURL(_ignore_static=True).js_router | tojson }},
            session: {{ urls.UHSessionModifAddMaterials.getURL(_ignore_static=True).js_router | tojson }},
            conference: {{ urls.UHConfModifAddMaterials.getURL(_ignore_static=True).js_router | tojson }},
            category: {{ urls.UHCategoryAddMaterial.getURL(_ignore_static=True).js_router | tojson }}
        },

        RoomBookingBookRoom: {{ url_rule_to_js('rooms.room_book') | tojson }},
        RoomBookingBook: {{ url_rule_to_js('rooms.book') | tojson }},
        RoomBookingDetails: {{ urls.UHRoomBookingRoomDetails.getURL(_ignore_static=True).js_router | tojson }},
        RoomBookingCloneBooking: {{ url_rule_to_js('rooms.roomBooking-cloneBooking')  | tojson }},
        ConfModifSchedule: {{ urls.UHConfModifSchedule.getURL(_ignore_static=True).js_router | tojson }},
        SubcontrModif: {{ urls.UHContribModifSubCont.getURL(_ignore_static=True).js_router | tojson }},
        AuthorDisplay: {{ urls.UHContribAuthorDisplay.getURL(_ignore_static=True).js_router | tojson }},
        AuthorEmail: {{ urls.UHConferenceEmail.getURL(_ignore_static=True).js_router | tojson }}
    },

    Data: {
        MaterialTypes: {{ material_types | tojson }},
        WeekDays: {{ [ "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday" ] }},
        DefaultLocation: {{ default_location | tojson }},
        Locations: {{ locations | tojson }}
    },

    Security:{
        allowedTags: "{{ ",".join(security_tools.allowedTags) }}",
        allowedAttributes: "{{ ",".join(security_tools.allowedAttrs) }}",
        allowedCssProperties: "{{ ",".join(security_tools.allowedCssProperties) }}",
        allowedProtocols: "{{ ",".join(security_tools.allowedProtocols) }}",
        urlProperties: "{{ ",".join(security_tools.urlProperties) }}",
        sanitizationLevel: {{ config.getSanitizationLevel() }}
    },

    Settings: {
        ExtAuthenticators: {{ ext_authenticators | tojson }},
        RoomBookingModuleActive: {{ config.getIsRoomBookingActive() | tojson }}
    },

    FileRestrictions: {
        MaxUploadFilesTotalSize: {{ config.getMaxUploadFilesTotalSize() }},
        MaxUploadFileSize: {{ config.getMaxUploadFileSize() }}
    },

    PDFConversion: {
        AvailablePDFConversions: {{file_converter.CDSConvFileConverter.getAvailableConversions()}},
        HasFileConverter: {{ config.hasFileConverter() | tojson }}
    }

};

{{ template_hook('vars-js') }}
