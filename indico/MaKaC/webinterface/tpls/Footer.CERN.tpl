<% import MaKaC.common.Configuration as Configuration %>
<%
if dark is not UNDEFINED:
    dark_ = dark
else:
    dark_ = False;
%>

% if isFrontPage:
    <div id="policyOfUse">
        <h1>${ _("Policy of Use")}</h1>
        ${ _("If you want to use it for CERN-related projects, please contact")} <a href="mailto:indico-support@cern.ch"> ${ _("Indico support")}</a>${ _(""".
        Non-CERN institutes may install the Indico software locally under GNU General Public License
        (see the""")} <a href="http://cern.ch/indico">${ _("project web site")}</a>).
    </div>
% endif

<div id="footer" class="${"longFooter " if shortURL != "" and not isFrontPage else ""}footer${" footerDark" if dark_ == True else ""}">
<%block name="footer">
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
</div>
% if Configuration.Config.getInstance().getWorkerName()!="":
  <!-- worker: ${ Configuration.Config.getInstance().getWorkerName() } -->
% endif
