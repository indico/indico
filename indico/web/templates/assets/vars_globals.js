var Indico = {{ indico_vars | tojson }};

if (location.protocol == 'https:') {
    Indico.Urls.Base = {{ config.getBaseSecureURL() | string | tojson }};
} else {
    Indico.Urls.Base = {{ config.getBaseURL() | string | tojson }};
}

{{ template_hook('vars-js') }}
