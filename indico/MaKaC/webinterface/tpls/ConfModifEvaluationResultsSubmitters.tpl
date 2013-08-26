
<br/><br/>
<form action="${actionUrl}" name="ResultsSubmitters" method="POST">
  <table width="50%" align="center" class="evalationResultsSubmitters">
      <tr>
        <td class="groupTitle">${mode.title()} ${ _("submitters")}</td>
      </tr>
      <tr>
        <td>
          <br/><br/>
          <a class="greyLink checkAllSubmitters" data-state="true" href="#"> ${ _("all")}</a>
          /
          <a class="greyLink checkAllSubmitters" data-state="false" href="#"> ${ _("none")}</a>
          <br/><br/>
          % for s in submissions:
            <input type="checkbox" class="submitter" name="${inputCheckboxName}" value="${s.getId()}"
              ${'checked="checked"' if isModeSelect and (len(selectedSubmissions)<1 or s in selectedSubmissions) else ""}/>
            ${s.getSubmissionDate(str)} - <b>${s.getSubmitterName()}</b>
            ${" (modified on "+s.getModificationDate(str)+")" if s.getModificationDate()!=None else ""}
            <br/>
          % endfor
          <br/>
          <br/>
          <input class="btn" type="submit" ${inputSubmitStyle} name="${mode}" value="${mode}" id="resultsAction"/>
          <input class="btn" type="submit" name="cancel" value="${ _("cancel")}"/>
          <input type='hidden' id="action"/>
        </td>
      </tr>
  </table>
</form>
<script type="text/javascript">

$("input[name=remove]").click(function(e){
    new ConfirmPopup($T("Import evaluation"),$T("Are you sure you want to remove these submissions?".format('${mode}')), function(confirmed) {
        if(confirmed) {
            $("#action").attr("name", "remove").val("remove").appendTo($("[name=ResultsSubmitters]"));
            $("[name=ResultsSubmitters]").submit();
        }
    }).open();
    return false;
    });

  $('.checkAllSubmitters').on('click', function(e) {
      e.preventDefault();
      $('.submitter').prop('checked', $(this).data('state'));
  });
</script>
<br/><br/>
