<%inherit file="Footer.tpl"/>
<%block name="footer_classes">footerCERN</%block>
<%block name="footer">
    % if isFrontPage:
        <div id="policyOfUse">
            <h1>${ _("Policy of Use")}</h1>
            ${ _("If you want to use it for CERN-related projects, please contact")} <a href="mailto:indico-support@cern.ch"> ${ _("Indico support")}</a>${ _(""".
            Non-CERN institutes may install the Indico software locally under GNU General Public License
            (see the""")} <a href="http://cern.ch/indico">${ _("project web site")}</a>).
        </div>
    % endif

    <a id="cern_link" href="http://cern.ch">
        <img src="${ systemIcon("cern_small_light" if is_meeting else "cern_small") }" alt="${ _("Indico")}" class="cern_logo" style="vertical-align: middle; margin: 15px;">
    </a>
    <div class="text" style="width: 200px">
        ${ _("Powered by ")} <a href="http://indico-software.org">Indico</a>
        <br/>
        <a href="${ url_for('legal.display') }">${ _("Terms and conditions") }</a>
    </div>
</%block>
