
<div id="tooltipPool" style="display:none">
  <div id="mainInformationHelp" class="tip">
     ${ _("Main information: e.g. title, contact info, announcement, ...")}<br/><br/>
    <u> ${ _("Note")}:</u><br/>
     ${ _("In order to prevent some misunderstanding the status and the dates are not imported.")}
  </div>
</div>

<br/><br/>
<form action="${actionUrl}" name="ResultsSubmitters" method="POST" enctype="multipart/form-data">
  <table width="50%" align="center" class="evalationSetupImportXml">
    <tr>
      <td class="groupTitle"> ${ _("Evaluation importation")}</td>
    </tr>
    <tr>
      <td class="blacktext">
        <br/>
        <ul>
          <li>
            <b>main setup configuration</b>
            ${contextHelp("mainInformationHelp")}
            <br/><br/>
            <input type="radio" name="configOption" value="current" checked="checked"/>
             ${ _("keep current one")}<br/>
            <input type="radio" name="configOption" value="imported"/>
             ${ _("overwrite with imported one <small>(loss of data!)</small>")}<br/>
            <br/><br/>
          </li>
          <li>
            <b> ${ _("questions")}</b>
            ${inlineContextHelp(_("Note&#58; If you select <i>keep only imported ones</i>, your current submissions will also be lost!"))}
            <br/><br/>
            <input type="radio" name="questionsOption" value="current" checked="checked"/>
             ${ _("keep only current ones")}<br/>
            <input type="radio" name="questionsOption" value="imported"/>
             ${ _("keep only imported ones <small>(loss of data!)</small>")}<br/>
            <input type="radio" name="questionsOption" value="both"/>
             ${ _("keep both")}<br/>
            <br/><br/>
          </li>
        </ul>
        <input type="file" name="xmlFile" size="80"/>
        <br/><br/><br/>
        <input class="btn" type="submit" name="importedXML" id="importedXML" value="${ _("import")}"/>
        <input class="btn" type="submit" name="cancel" value="${ _("cancel")}"/>
      </td>
    </tr>
  </table>
</form>
<script type="text/javascript">
$("#importedXML").click(function(){
    var self = this;
    if (document.ResultsSubmitters.xmlFile.value==""){
        new AlertPopup($T("Warning"), $T("Please select a file before importing.")).open();
        return false;
    }
    if ($("[name=configOption][value=imported]").attr("checked") == "checked" || $("[name=questionsOption][value=imported]").attr("checked") == "checked" ){
        new ConfirmPopup($T("Import evaluation"),$T("You will lose some data from your current evaluation! Are you sure you want to proceed?"), function(confirmed) {
            if(confirmed) {
                $("[name=ResultsSubmitters]").submit();
            }
        }).open();
        return false;
    }
});
</script>
<br/><br/>
