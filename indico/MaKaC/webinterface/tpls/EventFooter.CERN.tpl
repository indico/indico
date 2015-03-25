<%inherit file="Footer.CERN.tpl" />

<%block name="footer">
% if showSocial:
    <%include file="events/include/SocialIcons.tpl" args="dark=dark,url=shortURL,icalURL=icalURL,app_data=app_data"/>
% endif
    ${parent.footer()}
</%block>
