
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
              ${'checked="checked"' if isModeSelect and (selectedSubmissions is None or s.getId() in selectedSubmissions) else ""}/>
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

% if mode == 'remove':
    $("#resultsAction").click(function(){
        new ConfirmPopup($T("Import evaluation"), $T("Are you sure you want to remove these submissions?"), function(confirmed) {
            if(confirmed) {
                var actionField = '<input name="${mode}" value="${mode}" type="hidden">';
                $("form[name=ResultsSubmitters]").append(actionField).submit();
            }
        }).open();
        return false;
    });
% endif

$('.checkAllSubmitters').on('click', function(e) {
    e.preventDefault();
    $('.submitter').prop('checked', $(this).data('state'));
});
</script>
<br/><br/>