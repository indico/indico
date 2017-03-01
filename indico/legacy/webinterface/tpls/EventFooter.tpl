<%inherit file="Footer.tpl" />

<%block name="footer">
% if showSocial:
    <%include file="events/include/SocialIcons.tpl" args="dark=dark,url=shortURL,icalURL=icalURL,social_settings=social_settings"/>
% endif
    ${parent.footer()}
</%block>
