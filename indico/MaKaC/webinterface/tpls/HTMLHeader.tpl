<!DOCTYPE html>

<% baseUrl = baseurl if baseurl else "static" %>

<html xmlns:fb="http://ogp.me/ns/fb#" xmlns:og="http://opengraph.org/schema/">
    <head>
        <title>${ page._getTitle() }${ area }</title>
        <meta http-equiv="X-UA-Compatible" content="IE=edge" />
        <link rel="shortcut icon" type="image/x-icon" href="${ systemIcon('addressBarIcon') }">

        <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
        <meta content="${_session.csrf_token}" name="csrf-token" id="csrf-token">

% if social.get('facebook', {}).get('appId', None):
        <meta property="fb:app_id" content="${social['facebook']['appId']}"/>
% endif

% if baseUrl == 'static':
        <script type="text/javascript">
        window.indicoOfflineSite = true;
        </script>
% endif

        <script>
            var ScriptRoot = ${ conf.getScriptBaseURL() | n,j };
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

        <!-- page-specific CSS files-->
        % for cssFile in extraCSS:
            <link rel="stylesheet" type="text/css" href="${cssFile}">
        % endfor

        % for cssFile in printCSS:
            <link rel="stylesheet" type="text/css" media="print" href="${cssFile}">
        % endfor

        ${ template_hook('html-head', template=self) }
    </head>
    <body data-user-id="${ user.getId() if user else 'null' }" data-debug="${ _app.debug|n,j }">
        ${ page._getWarningMessage() }
