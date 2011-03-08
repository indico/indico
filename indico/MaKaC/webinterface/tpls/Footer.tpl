<% import MaKaC.common.Configuration as Configuration %>
<%
if dark is not UNDEFINED:
    dark_ = dark
else:
    dark_ = False;
%>

<!-- TODO: remove? -->
<script type="text/javascript">
function envoi(){
    //alert('Le code de la langue choisie est '+document.forms["changeSesLang"].elements["lang"].value)
    document.forms["changeSesLang"].submit()
}
</script>

<div id="poweredBy" class="${"longFooter " if shortURL != "" and not isFrontPage else ""}footer${" footerDark" if dark_ == True else ""}">

<div style="margin-bottom: 15px; font-family: monospace; font-size: 10px;">
  % if shortURL != "" and not isFrontPage:
  <div>${ shortURL }</div>
  % endif

  % if modificationDate != "":
  <div>${ _("Last modified: ") + modificationDate }</div>
  % endif
</div>


            <img src="${ systemIcon("indico_small") }" alt="${ _("Indico - Integrated Digital Conference")}" style="vertical-align: middle; margin-right: 2px;"/>
            <span style="vertical-align: middle;">${ _("Powered by ")} <a href="http://cdsware.cern.ch/indico/">Indico</a></span>

            % if Configuration.Config.getInstance().getWorkerName()!="":
                <span style="display: none;">${ Configuration.Config.getInstance().getWorkerName() }</span>
            % endif

</div>
