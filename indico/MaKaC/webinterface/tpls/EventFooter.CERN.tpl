<%inherit file="Footer.CERN.tpl" />

<%block name="footer">
<script>
    $(document).ready(function() {
        $('h1, .subLevelTitle, .subEventLevelTitle, .topLevelTitle').mathJax();
    });
</script>
% if showSocial:
    <%include file="events/include/SocialIcons.tpl" args="dark=dark,url=shortURL,icalURL=icalURL,app_data=app_data"/>
% endif
    ${parent.footer()}
</%block>
