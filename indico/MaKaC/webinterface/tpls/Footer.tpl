<% import MaKaC.common.Configuration as Configuration %>
<%
if dark is not UNDEFINED:
    dark_ = dark
else:
    dark_ = False;
%>

<div id="footer" class="${"longFooter " if shortURL != "" and not isFrontPage else ""}footer${" footerDark" if dark_ == True else ""}">
  <%block name="footer">
          <img src="${ systemIcon("indico_small") }" alt="${ _("Indico - Integrated Digital Conference")}" style="vertical-align: middle; margin-right: 2px;"/>
            <span style="vertical-align: middle;">${ _("Powered by ")} <a href="http://indico-software.org">Indico</a></span>
  </%block>
</div>
% if Configuration.Config.getInstance().getWorkerName()!="":
  <!-- worker: ${ Configuration.Config.getInstance().getWorkerName() } -->
% endif
