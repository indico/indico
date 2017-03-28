<%
if dark is not UNDEFINED:
    dark_ = dark
else:
    dark_ = False;
%>
<div id="footer" class="${"longFooter " if shortURL != "" and not isFrontPage else ""}footer${" footerDark" if dark_ == True else ""} <%block name="footer_classes"></%block>">

    <%block name="footer">
        <img src="${ systemIcon("indico_small") }" alt="${ _("Indico")}" style="vertical-align: middle; margin-right: 2px;"/>
        <span>${ _("Powered by ")} <a href="http://indico-software.org">Indico</a></span>
        ${ template_hook('page-footer') }
    </%block>
</div>

% if 'injected_js' in _g:
    ${'\n'.join(_g.injected_js)}
% endif
