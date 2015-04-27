<!DOCTYPE html>

<% baseUrl = baseurl if baseurl else "static" %>

<html xmlns:fb="http://ogp.me/ns/fb#" xmlns:og="http://opengraph.org/schema/">
    <head>
        <title>${ page._getTitle() }${ area }</title>
        <meta http-equiv="X-UA-Compatible" content="IE=edge" />
        <link rel="shortcut icon" type="image/x-icon" href="${ systemIcon('addressBarIcon') }">

        <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
        <meta content="${self_._rh.csrf_token}" name="csrf-token" id="csrf-token"/>

% if social.get('facebook', {}).get('appId', None):
        <meta property="fb:app_id" content="${social['facebook']['appId']}"/>
% endif

% if baseUrl == 'static':
        <script type="text/javascript">
        window.indicoOfflineSite = true;
        </script>
% endif

        <script type="text/javascript">
            var ScriptRoot = "${ baseUrl }/js/";
        </script>
        <script type="text/javascript" src="${ url_for('assets.i18n_locale', locale_name=language) }"></script>
        <script type="text/javascript" src="${ url_for('assets.js_vars_global') }"></script>

        <!-- page-specific JS files -->
        % for js_file in extraJSFiles:
            <script type="text/javascript" src="${ js_file }"></script>
        % endfor

        <!--[if (gte IE 6)&(lte IE 8)]>
        % for JSFile in assets["ie_compatibility"].urls():
            ${'<script src="'+ baseurl + JSFile +'" type="text/javascript"></script>\n'}
        % endfor
        <![endif]-->

        <!-- page-specific CSS files-->
        % for cssFile in extraCSS:
            <link rel="stylesheet" type="text/css" href="${cssFile}">
        % endfor

        <!-- page-specific, directly inserted Javascript -->
        <script>
            ${ "\n\n".join(extraJS) }
        </script>

        <!-- global JS variables -->
        <script>
        % if user:
            IndicoGlobalVars.isUserAuthenticated = true;
        % else:
            IndicoGlobalVars.isUserAuthenticated = false;
        % endif
        </script>

        <script type="text/javascript" src="${ url_for('assets.js_vars_user') }"></script>

        <!-- other page-specific things -->
        ${ page._getHeadContent() }

        ${ template_hook('html-head', template=self) }
    </head>
    <body data-user-id="${ user.getId() if user else 'null' }">
        ${ page._getWarningMessage() }
