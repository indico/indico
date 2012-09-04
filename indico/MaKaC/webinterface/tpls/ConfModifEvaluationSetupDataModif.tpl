<!-- context help dialogs : start -->
<div id="tooltipPool" style="display:none">
  <div id="anonymousHelp" class="tip">
    ${ _("Can logged submitters send their form anonymously?")}<br/><br/>
    <em>${ _("Hint")}:</em><br/>
    ${ _("When anonymous you should get more answers.")}<br/>
    <em>${ _("Note")}:</em><br/>
    ${ _("Users not logged in can always send their form anonymously.")}<br/>
    ${ _("If you really need to know the identity of all your submitters, you have to check the option <strong>Must&nbsp;have&nbsp;an&nbsp;account")}</strong>.
  </div>
  <div id="accountHelp" class="tip">
    ${ _("Is an account needed?")}<br/><br/>
    <em>${ _("Hint")}:</em><br/>
    ${ _("If yes visitors must first login before accessing the form.")}
  </div>
  <div id="notificationHelp" class="tip">
    ${ _("When the evaluation starts, following emails are notified.")}<br/><br/>
    <em>${ _("Note")}:</em><br/>
    ${ _("No notification is sent if your evaluation is not ready (i.e. contains no question)!")}
  </div>
</div>
<!-- context help dialogs : end -->

<form name="DataModif" method="POST" action="${postURL}">
  <table class="groupTable">
    <tr>
      <td class="groupTitle" colspan="2">${ _("Modify Evaluation")}</td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Start date")}</span></td>
      <td bgcolor="white" width="100%">
                <span id="sDatePlace"></span>
                <input type="hidden" value="${ sDay }" name="sDay" id="sDay"/>
                <input type="hidden" value="${ sMonth }" name="sMonth" id="sMonth"/>
                <input type="hidden" value="${ sYear }" name="sYear" id="sYear"/>
       </td>
    </tr>
    <tr>
      <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("End date")}</span></td>
      <td bgcolor="white" width="100%">
                <span id="eDatePlace"></span>
                <input type="hidden" value="${ eDay }" name="eDay" id="eDay"/>
                <input type="hidden" value="${ eMonth }" name="eMonth" id="eMonth"/>
                <input type="hidden" value="${ eYear }" name="eYear" id="eYear"/>
      </td>
    </tr>
    <tr>
      <td class="titleCellTD"><span class="titleCellFormat">${ _("Title")}</span><span class="mandatoryField"> *</span></td>
      <td class="modifRight"><input type="text" size="50" name="title" id="title" value="${title}"/></td>
    </tr>
    <tr>
      <td class="titleCellTD"><span class="titleCellFormat">${ _("Announcement")}</span></td>
      <td class="notifMain"><textarea name="announcement" cols="80" rows="10">${announcement}</textarea></td>
    </tr>
    <tr>
      <td class="titleCellTD"><span class="titleCellFormat">${ _("Max number of submissions")}</span></td>
      <td class="modifRight"><input type="text" size="10" name="submissionsLimit" value="${submissionsLimit}"/>
      ${ _("(0 or nothing for unlimited)")}
      </td>
    </tr>
    <tr>
      <td class="titleCellTD"><span class="titleCellFormat">${ _("Contact info")}</span></td>
      <td class="modifRight"><input type="text" size="50" name="contactInfo" value="${contactInfo}"/></td>
    </tr>
    <tr>
      <td class="titleCellTD"><span class="titleCellFormat">${ _("Email notifications")}</span></td>
      <td class="modifRight">
        <table class="notificationEdit">
          <tr>
            <td class="notifTitle" colspan="3">${ _("Start of evaluation")}</td>
          </tr>
          <tr>
            <td class="notifLeft">${ _("To")}:</td>
            <td class="notifMain">
              <input type="checkbox" name="notifyAllAdherents"/>Add&nbsp;current&nbsp;${adherent}s
              <textarea name="evaluationStartNotifyTo" id="evaluationStartNotifyTo" rows="5" cols="15">${evaluationStartNotifyTo}</textarea>
            </td>
            <td class="notifRight">
              ${contextHelp("notificationHelp")}
            </td>
          </tr>
          <tr>
            <td class="notifLeft">${ _("Cc")}:</td>
            <td class="notifMain">
              <textarea name="evaluationStartNotifyCc" id="evaluationStartNotifyCc" rows="5" cols="15">${evaluationStartNotifyCc}</textarea>
            </td>
            <td></td>
          </tr>
          <tr>
            <td class="notifTitle" colspan="3" style="padding-top:10px;">${ _("New submission")}</td>
          </tr>
          <tr>
            <td class="notifLeft">${ _("To")}:</td>
            <td class="notifMain">
              <textarea name="newSubmissionNotifyTo" id="newSubmissionNotifyTo" rows="5" cols="15">${newSubmissionNotifyTo}</textarea>
            </td>
            <td>${inlineContextHelp(_("When a new submission arrives, notify following emails (separated by commas)."))}</td>
          </tr>
          <tr>
            <td class="notifLeft">${ _("Cc")}:</td>
            <td class="notifMain">
              <textarea name="newSubmissionNotifyCc" id="newSubmissionNotifyCc" rows="5" cols="15">${newSubmissionNotifyCc}</textarea>
            </td>
            <td></td>
          </tr>
        </table>
      </td>
    </tr>
    <tr>
      <td class="titleCellTD"><span class="titleCellFormat">${ _("Must have an account")}</span></td>
      <td class="modifRight">
        <input type="checkbox" name="mandatoryAccount" ${mandatoryAccount}/>
        ${contextHelp("accountHelp")}
      </td>
    </tr>
    <tr>
      <td class="titleCellTD"><span class="titleCellFormat">${ _("Anonymous")}</span></td>
      <td class="modifRight">
        <input type="checkbox" name="anonymous" ${anonymous} />
        ${contextHelp("anonymousHelp")}
      </td>
    </tr>

    <tr><td>&nbsp;</td></tr>
    <tr>
      <td colspan="2">
        <table>
          <tr>
            <td><input type="submit" class="btn" name="modify" value="${ _("ok")}" id="ok"/></td>
            <td><input type="submit" class="btn" name="cancel" value="${ _("cancel")}"/></td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</form>

<script type="text/javascript">
    var parameterManager = new IndicoUtil.parameterManager();
    parameterManager.add($E('title'), 'text', false);
    parameterManager.add($E('evaluationStartNotifyTo'), 'emaillist', true);
    parameterManager.add($E('evaluationStartNotifyCc'), 'emaillist', true);
    parameterManager.add($E('newSubmissionNotifyTo'), 'emaillist', true);
    parameterManager.add($E('newSubmissionNotifyCc'), 'emaillist', true);

    $("#ok").click(function() {
        if (!parameterManager.check())
            event.preventDefault();
    });
    IndicoUI.executeOnLoad(function()
    {

        var startDate = IndicoUI.Widgets.Generic.dateField(false,null,['sDay', 'sMonth', 'sYear']);
        $E('sDatePlace').set(startDate);

        var endDate = IndicoUI.Widgets.Generic.dateField(false,null,['eDay', 'eMonth', 'eYear']);
        $E('eDatePlace').set(endDate);

        % if sDay != '':
            startDate.set('${ sDay }/${ sMonth }/${ sYear }');
        % endif

        % if eDay != '':
            endDate.set('${ eDay }/${ eMonth }/${ eYear }');
        % endif

     });

</script>