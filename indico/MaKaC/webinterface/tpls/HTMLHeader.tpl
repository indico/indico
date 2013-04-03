<!DOCTYPE html>
<html xmlns:fb="http://ogp.me/ns/fb#" xmlns:og="http://opengraph.org/schema/">
    <head>
        <title>${ page._getTitle() }${ area }</title>
        <meta http-equiv="X-UA-Compatible" content="IE=edge" />
        <link rel="shortcut icon" type="image/x-icon" href="${ systemIcon('addressBarIcon') }">

        <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>

% if social.get('facebook', {}).get('appId', None):
        <meta property="fb:app_id" content="${social['facebook']['appId']}"/>
% endif

% if analyticsActive and analyticsCodeLocation == "head":
        ${analyticsCode}
% endif

        <script type="text/javascript">
                var TextRoot = "${ baseurl }/js/indico/i18n/";
                var ScriptRoot = "${ baseurl }/js/";
        </script>

        <!-- Indico specific -->
        ${ page._getJavaScriptInclude(baseurl + "/JSContent.py/getVars") } <!-- Indico Variables -->

        <!-- Page Specific JS files-->
        % for JSFile in extraJSFiles:
            ${ page._getJavaScriptInclude(baseurl + JSFile) }
        % endfor

        <!--[if (gte IE 6)&(lte IE 8)]>
        % for JSFile in assets["selectivizr"].urls():
            ${'<script src="'+ baseurl + JSFile +'" type="text/javascript"></script>\n'}
            <noscript><link rel="stylesheet" href="[fallback css]" /></noscript>
        % endfor
        <![endif]-->

    <script type="text/javascript">
      var currentLanguage = '${ language }';
      loadDictionary(currentLanguage);
    </script>

        <!-- Calendar Widget -->
        ${ page._getJavaScriptInclude(baseurl + "/js/calendar/calendar.js") }
        ${ page._getJavaScriptInclude(baseurl + "/js/calendar/calendar-setup.js") }

        <!-- Page Specific CSS files-->
        % for cssFile in extraCSS:
            <link rel="stylesheet" type="text/css" href="${baseurl}/${cssFile.lstrip('/')}">
        % endfor

        <!-- Page Specific, directly inserted Javascript -->
        <script type="text/javascript">
            ${ "\n\n".join(extraJS) }
        </script>

        <!-- Indico page-wide global JS variables -->
        <script type="text/javascript">
        <% user = page._rh.getAW().getUser() %>
        % if user:
            IndicoGlobalVars.isUserAuthenticated = true;
            IndicoGlobalVars.userData = ${ jsonEncode(page._getJavaScriptUserData()) };
        % else:
            IndicoGlobalVars.isUserAuthenticated = false;
        % endif
        </script>

        <!-- Other Page Specific -->
        ${ page._getHeadContent() }
    </head>
    <body>
        ${ page._getWarningMessage() }
    % if analyticsActive and analyticsCodeLocation == "body":
        ${analyticsCode}
    % endif
