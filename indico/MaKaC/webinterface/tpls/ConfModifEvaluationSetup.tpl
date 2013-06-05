<table>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Current status")}</span></td>
    <td class="blacktext" colspan="2">
      <form action="${setStatusURL}" method="post">
          <div>
            <input name="changeTo" type="hidden" value="${changeTo}"/>
            <strong>${status}</strong> ${statusMoreInfo}
            <span style="margin-right:10px;" id="statusHelp"></span>
            <small><input type="submit" class="btn" value="${changeStatus}"/></small>
        </div>
      </form>
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Evaluation start date")}</span></td>
    <td class="blacktext" ${'id="hiddenNoDate"' if not evaluation.isVisible() else ""} colspan="2">
      ${startDate}
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Evaluation end date")}</span></td>
    <td class="blacktext" colspan="2">${endDate}</td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Title")}</span></td>
    <td class="blacktext" colspan="2">${title}</td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Contact info")}</span></td>
    <td class="blacktext" colspan="2">${evaluation.getContactInfo()}</td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Announcement")}</span></td>
    <td class="blacktext" colspan="2">
        <pre>
          % if evaluation.getAnnouncement():
              ${ evaluation.getAnnouncement() }
      % endif
    </pre>
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Max number of submissions")}</span></td>
    <td class="blacktext" colspan="2">${submissionsLimit}</td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Email notifications")}</span></td>
    <td colspan="2">
      <span style="font-weight:bold;" id="startEvaluation">${ _("start of evaluation")}</span>
      <table class="notificationShow">
        <tr>
          <td class="blacktext"> ${ _("To")}:</td>
          <td class="small">${evaluationStartNotifyTo}</td>
        </tr>
        <tr>
          <td class="blacktext"> ${ _("Cc")}:</td>
          <td class="small">${evaluationStartNotifyCc}</td>
        </tr>
      </table>
      <br/>
      <span style="font-weight:bold;" id="newSubmission">${ _("new submission")}</span>
      <table class="notificationShow">
        <tr>
          <td class="blacktext"> ${ _("To")}:</td>
          <td class="small">${newSubmissionNotifyTo}</td>
        </tr>
        <tr>
          <td class="blacktext"> ${ _("Cc")}:</td>
          <td class="small">${newSubmissionNotifyCc}</td>
        </tr>
      </table>
    </td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Must have an account")}</span></td>
    <td class="blacktext" colspan="2" id="mustHaveAccountField">${mandatoryAccount}</td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Anonymous")}</span></td>
    <td class="blacktext" id="anonymousField">${anonymous}</td>
    <td valign="bottom" align="right">
      <form action="${dataModificationURL}" method="post">
          <div>
              <input type="submit" class="btn" value="${ _("modify")}"/>
          </div>
      </form>
    </td>
  </tr>
  <tr>
    <td colspan="3" class="horizontalLine">&nbsp;</td>
  </tr>
  <tr>
    <td class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Special Actions")}</span></td>
    <td class="blacktext" colspan="2">
      <table class="evalSetupSpecialActions">
        <tr>
          <td>
            <form action="${specialActionURL}" method="post">
                <div>
                    <input type="submit" class="btn" name="exportXML" value="${ _("export evaluation")}"/>
                </div>
            </form>
          </td>
          <td> ${ _("Export the evaluation with its questions to an XML file.")}</td>
        </tr>
        <tr>
          <td>
            <form action="${specialActionURL}" method="post">
                <div>
                      <input type="submit" class="btn" name="importXML" value="${ _("import evaluation")}"/>
                  </div>
            </form>
          </td>
          <td> ${ _("Import an evaluation from an XML file.")}</td>
        </tr>
        <tr>
          <td>
            <form action="${specialActionURL}" method="post">
                    <div>
                          <input type="hidden" name="removeSubmissions" value="removeSubmissions"/>
                          <input type="submit" class="btn" name="submitbtn" id="removeSubmissions" value="${ _("remove submissions")}"
                  onmouseover="this.style.color='red'" onmouseout="this.style.color='#234173'"/>
                     </div>
            </form>
          </td>
          <td> ${ _("All collected answers will be erased.")}</td>
        </tr>
        <tr>
          <td>
            <form action="${specialActionURL}" method="post">
                  <div>
                    <input type="hidden" name="removeQuestions" value="removeQuestions"/>
                    <input type="submit" class="btn" name="submitbtn" id="removeQuestions" value="${ _("remove questions")}"
                  onmouseover="this.style.color='red'" onmouseout="this.style.color='#234173'"/>
                </div>
            </form>
          </td>
          <td>
             ${ _("All questions will be erased. As the submissions are connected to them, they will also be removed!")}
          </td>
        </tr>
        <tr>
          <td>
            <form action="${specialActionURL}" method="post">
                <div>
                      <input type="hidden" name="reinit" value="reinit"/>
                      <input type="submit" class="btn" name="submitbtn" id="reinit" value="${ _("reinit evaluation")}"
                  onmouseover="this.style.color='red'" onmouseout="this.style.color='#234173'"/>
                </div>
            </form>
          </td>
          <td> ${ _("Delete all evaluation informations, its questions and its submissions.")}</td>
        </tr>
      </table>
    </td>
  </tr>
  <tr>
    <td colspan="3" class="horizontalLine">&nbsp;</td>
  </tr>
</table>
<br/>
<script type="text/javascript">
    $("#removeSubmissions").click(function(){
        var self = this;
        new ConfirmPopup($T("Remove Submissions"),$T("Are you sure you want to remove all submissions?"), function(confirmed) {
            if(confirmed) {
                $(self).closest("form").submit();
            }
        }).open();
        return false;
    });
    $("#removeQuestions").click(function(){
        var self = this;
        new ConfirmPopup($T("Remove Questions"),$T("Are you sure you want to remove all questions? Be aware that the submissions will also be deleted!"), function(confirmed) {
            if(confirmed) {
                $(self).closest("form").submit();
            }
        }).open();
        return false;
    });
    $("#reinit").click(function(){
        var self = this;
        new ConfirmPopup($T("Reset evaluation"),$T("Are you sure you want to reset the evaluation?"), function(confirmed) {
            if(confirmed) {
                $(self).closest("form").submit();
            }
        }).open();
        return false;
    });
</script>