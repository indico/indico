
<br/><br/>
<form action="${actionUrl}" name="ResultsSubmitters" method="POST">
  <table width="50%" align="center" class="evalationResultsSubmitters">
      <tr>
        <td class="groupTitle">${mode.title()} ${ _("submitters")}</td>
      </tr>
      <tr>
        <td>
          <br/><br/>
          <a class="greyLink" href="javascript:check(document.ResultsSubmitters.${inputCheckboxName}, true)"> ${ _("all")}</a>
          /
          <a class="greyLink" href="javascript:check(document.ResultsSubmitters.${inputCheckboxName}, false)"> ${ _("none")}</a>
          <br/><br/>
          % for s in submissions:
            <input type="checkbox" name="${inputCheckboxName}" value="${s.getId()}"
              ${'checked="checked"' if isModeSelect and (len(selectedSubmissions)<1 or s in selectedSubmissions) else ""}/>
            ${s.getSubmissionDate(str)} - <b>${s.getSubmitterName()}</b>
            ${" (modified on "+s.getModificationDate(str)+")" if s.getModificationDate()!=None else ""}
            <br/>
          % endfor
          <br/>
          <br/>
          <input class="btn" type="submit" ${inputSubmitStyle} name="${mode}" value="${mode}" id="resultsAction"/>
          <input class="btn" type="submit" name="cancel" value="${ _("cancel")}"/>
        </td>
      </tr>
  </table>
</form>
<script type="text/javascript">

$("#resultsAction").click(function(){
    new ConfirmPopup($T("Import evaluation"),$T("Are you sure you want to remove these submissions?"), function(confirmed) {
        if(confirmed) {
            $("[name=ResultsSubmitters]").submit();
        }
    }).open();
    return false;
    });

  <!--check/uncheck a group of checkboxes-->
  function check(field, isChecked){
    for (i=0; i < field.length; i++)
      field[i].checked = isChecked ;
  }
</script>
<br/><br/>
