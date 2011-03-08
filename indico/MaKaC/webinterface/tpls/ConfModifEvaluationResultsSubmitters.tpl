
<br/><br/>
<form action="${actionUrl}" name="ResultsSubmitters" method="POST" ${submitConfirm}>
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
          <input class="btn" type="submit" ${inputSubmitStyle} name="${mode}" value="${mode}" onclick="submitIsClicked(true);"/>
          <input class="btn" type="submit" name="cancel" value="${ _("cancel")}" onclick="submitIsClicked(false);"/>
        </td>
      </tr>
  </table>
</form>
<script type="text/javascript">
  <!--to know which submit button ("submit"/"cancel") has been pressed.-->
  var isSubmitClicked = false;
  function submitIsClicked(val){ isSubmitClicked = val; }
  <!--when removing, ask to confirm.-->
  function confirmation(){
    if (isSubmitClicked)
      return confirm('${ _("Are you sure you want to remove these submissions?")}');
    else return true;
  }
  <!--check/uncheck a group of checkboxes-->
  function check(field, isChecked){
    for (i=0; i < field.length; i++)
      field[i].checked = isChecked ;
  }
</script>
<br/><br/>
