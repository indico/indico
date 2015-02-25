var Indico = {{ indico_vars | tojson }};

if (location.protocol == 'https:') {
    Indico.Urls.Base = {{ config.getBaseSecureURL() | string | tojson }};
    Indico.Urls.JsonRpcService = {{ url_handlers.UHJsonRpcService.getURL(secure=True) | string | tojson }};
    Indico.Urls.ExportAPIBase = {{ url_handlers.UHAPIExport.getURL(secure=True) | string | tojson }};
    Indico.Urls.APIBase = {{ url_handlers.UHAPIAPI.getURL(secure=True) | string | tojson }};
} else {
    Indico.Urls.Base = {{ config.getBaseURL() | string | tojson }};
    Indico.Urls.JsonRpcService = {{ url_handlers.UHJsonRpcService.getURL() | string | tojson }};
    Indico.Urls.ExportAPIBase = {{ url_handlers.UHAPIExport.getURL() | string | tojson }};
    Indico.Urls.APIBase = {{ url_handlers.UHAPIAPI.getURL() | string | tojson }};
}

{{ template_hook('vars-js') }}
