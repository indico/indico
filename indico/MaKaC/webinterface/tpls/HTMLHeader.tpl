<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
            "http://www.w3.org/TR/html4/loose.dtd">
<html xmlns:fb="http://ogp.me/ns/fb#" xmlns:og="http://opengraph.org/schema/">
    <head>
        <title>${ page._getTitle() }${ area }</title>
        <meta http-equiv="X-UA-Compatible" content="IE=8" />

        <link rel="shortcut icon" type="image/x-icon" href="${ systemIcon('addressBarIcon') }">
        <link rel="stylesheet" type="text/css" href="${ baseurl }/css/calendar-blue.css" >
        <link rel="stylesheet" type="text/css" href="${ baseurl }/css/jquery-ui.css">
        <link rel="stylesheet" type="text/css" href="${ baseurl }/css/jquery.qtip.css">
        <link rel="stylesheet" type="text/css" href="${ baseurl }/css/jquery.colorbox.css">
        <link rel="stylesheet" type="text/css" href="${ baseurl }/css/jquery-ui-custom.css">

        <link rel="stylesheet" type="text/css" href="${ baseurl }/css/${ stylesheet }">

        <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>

% if social.get('facebook', {}).get('appId', None):
        <meta property="fb:app_id" content="${social['facebook']['appId']}"/>
% endif

        <script type="text/javascript">
                var TextRoot = "${ baseurl }/js/indico/i18n/";
                var ScriptRoot = "${ baseurl }/js/";
        </script>

        <!-- Indico specific -->
        ${ page._getJavaScriptInclude(baseurl + "/JSContent.py/getVars") } <!-- Indico Variables -->

        <!-- Page Specific JS files-->
        % for JSFile in extraJSFiles:
            ${ page._getJavaScriptInclude(baseurl + '/' + JSFile) }
        % endfor

    <script type="text/javascript">
      var currentLanguage = '${ language }';
      loadDictionary(currentLanguage);
    </script>

        <!-- Tooltip -->
        <script type="text/javascript" src="${ baseurl }/js/tooltip/domLib.js"></script>
        <script type="text/javascript" src="${ baseurl }/js/tooltip/domTT.js"></script>
        <script type="text/javascript" src="${ baseurl }/js/tooltip/domTT_drag.js"></script>

        <!-- Calendar Widget -->
        ${ page._getJavaScriptInclude(baseurl + "/js/calendar/calendar.js") }
        ${ page._getJavaScriptInclude(baseurl + "/js/calendar/calendar-setup.js") }

        <!-- Page Specific CSS files-->
        % for cssFile in extraCSS:
            <link rel="stylesheet" type="text/css" href="${ baseurl + '/' + cssFile }">
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
