<%inherit file="Footer.tpl"/>
<%block name="footer">
    % if isFrontPage:
        <div id="policyOfUse">
            <h1>${ _("Policy of Use")}</h1>
            ${ _("If you want to use it for CERN-related projects, please contact")} <a href="mailto:indico-support@cern.ch"> ${ _("Indico support")}</a>${ _(""".
            Non-CERN institutes may install the Indico software locally under GNU General Public License
            (see the""")} <a href="http://cern.ch/indico">${ _("project web site")}</a>).
        </div>
    % endif
    <a id="cern_link" href="http://www.cern.ch">
      <img src="${ systemIcon("cern_small" if shortURL else "cern_small_light") }" alt="${ _("Indico - Integrated Digital Conference")}" class="cern_logo" style="vertical-align: middle; margin-right: 12px;"/>
    </a>
    <div class="text" style="width: 200px">${ _("Powered by ")} <a href="http://indico-software.org">Indico</a></div>

    % if extraFooterContent:
        % for extra in extraFooterContent:
            <%include file="${extra['path']}" args="extargs=extra['args']"/>
        % endfor
    % endif
</%block>
