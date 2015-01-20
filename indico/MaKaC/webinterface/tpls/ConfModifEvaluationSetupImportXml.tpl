
<div id="tooltipPool" style="display:none">
  <div id="mainInformationHelp" class="tip">
     ${ _("Main information: e.g. title, contact info, announcement, ...")}<br/><br/>
    <u> ${ _("Note")}:</u><br/>
     ${ _("In order to prevent some misunderstanding the status and the dates are not imported.")}
  </div>
</div>

<br/><br/>
<form action="${actionUrl}" id="ResultsSubmitters" method="POST" enctype="multipart/form-data">
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
$("#importedXML").on('click', function (e){
    if (!$('input[name="xmlFile"]').val()){
        new AlertPopup($T("Warning"), $T("Please select a file before importing.")).open();
        e.preventDefault();
        return;
    }
    if ($('input[name="configOption"]:checked').val() == 'imported' || $('input[name="questionsOption:checked"]').val() == 'imported' ){
        e.preventDefault();
        new ConfirmPopup($T("Import evaluation"), $T("You will lose some data from your current evaluation! Are you sure you want to proceed?"), function(confirmed) {
            if(confirmed) {
                var form = $('#ResultsSubmitters');
                $('<input/>', {
                    type: 'hidden',
                    name: 'importedXML',
                    value: 'import'
                }).appendTo(form);
                form.submit();
            }
        }).open();
    }
});
</script>
<br/><br/>
