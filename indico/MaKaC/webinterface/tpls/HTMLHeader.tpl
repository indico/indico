<% declareTemplate(newTemplateStyle=True) %>

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
            "http://www.w3.org/TR/html4/loose.dtd">
<html>
    <head>
        <title><%= page._getTitle() %><%= area %></title>
        <meta http-equiv="X-UA-Compatible" content="IE=8" />

        <link rel="shortcut icon" type="image/x-icon" href="<%= systemIcon('addressBarIcon') %>">
        <link rel="stylesheet" type="text/css" href="<%= baseurl %>/css/<%= stylesheet %>">
        <link rel="stylesheet" type="text/css" href="<%= baseurl %>/css/calendar-blue.css" >

        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">

        <script type="text/javascript">
                var TextRoot = "<%= baseurl %>/js/indico/i18n/";
                var ScriptRoot = "<%= baseurl %>/js/";
        </script>

        <!-- Indico specific -->
        <%= page._getJavaScriptInclude(baseurl + "/JSContent.py/getVars") %> <!-- Indico Variables -->

        <!-- Page Specific JS files-->
        <% for JSFile in extraJSFiles: %>
            <%= page._getJavaScriptInclude(baseurl + '/' + JSFile) %>
        <% end %>

	<script type="text/javascript">
	  currentLanguage = '<%= language %>';
	  loadDictionary(currentLanguage);
	</script>
        
        <!-- Tooltip -->
        <script type="text/javascript" src="<%= baseurl %>/js/tooltip/domLib.js"></script>
        <script type="text/javascript" src="<%= baseurl %>/js/tooltip/domTT.js"></script>
        <script type="text/javascript" src="<%= baseurl %>/js/tooltip/domTT_drag.js"></script>

        <!-- Calendar Widget -->
        <%= page._getJavaScriptInclude(baseurl + "/js/calendar/calendar.js") %>
        <%= page._getJavaScriptInclude(baseurl + "/js/calendar/calendar-setup.js") %>

        <!-- Page Specific CSS files-->
        <% for CSSFile in extraCSSFiles: %>
            <link rel="stylesheet" type="text/css" href="<%= baseurl %>/css/<%= CSSFile %>">
        <% end %>
        
        <!-- Page Specific, directly inserted CSS -->
        <style type="text/css">
            <%= "\n".join(extraCSS) %>
        </style>
        
        <!-- Page Specific, directly inserted Javascript -->
        <script type="text/javascript">
            <%= "\n\n".join(extraJS) %>
        </script>

        <!-- Other Page Specific -->
        <%= page._getHeadContent() %>
    </head>
    <body>
        <%= page._getWarningMessage() %>
