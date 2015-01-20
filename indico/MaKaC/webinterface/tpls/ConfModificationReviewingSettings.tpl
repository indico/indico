<% from MaKaC.paperReviewing import ConferencePaperReview %>
<% from MaKaC.paperReviewing import Template %>
<% from MaKaC.common.utils import formatDateTime %>
<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% import MaKaC.common.Configuration as Configuration %>
<table width="90%" border="0" style="padding-bottom:5px;">
    <tr>
        <td nowrap class="groupTitle">${ _("Step 1 - Choose type of paper reviewing")}
        </td>
    </tr>
</table>

<table style="padding-left: 20px; padding-bottom: 20px;">
    <tr>
        <td id="reviewingModeHelp" class="subGroupTitle" style="width:480px;">${ _("Type of reviewing")}</td>
    </tr>
    <tr>
        <td nowrap style="vertical-align:top; padding-top: 5px; padding-left:5px;">
            <span id="inPlaceEditReviewingMode" style="display:inline">${ ConferencePaperReview.reviewingModes[choice] }</span>
        </td>
    </tr>
</table>
% if ConfReview.hasReviewing():
    <% display = 'table' %>
% else:
    <% display = 'none' %>
% endif
<table id='steptitle' width="90%" border="0" style="padding-bottom:5px; display:${display}">
    <tr>
        <td class="groupTitle">
            ${ _("Step 2 - Set up the options for ")}<span id="title">
            ${ _("content reviewing") if ConferencePaperReview.reviewingModes[choice]==ConferencePaperReview.reviewingModes[2] else ""}
            ${ _("layout reviewing") if ConferencePaperReview.reviewingModes[choice]==ConferencePaperReview.reviewingModes[3] else ""}
            ${ _("content and layout reviewing") if ConferencePaperReview.reviewingModes[choice]==ConferencePaperReview.reviewingModes[4] else ""}
            </span>
        </td>
    </tr>
</table>
% if ConfReview.hasPaperReviewing():
    <% display = 'table' %>
% else:
    <% display = 'none' %>
% endif
<table id='statusTable' style="padding-left: 20px; padding-bottom: 20px; display:${display}">
    <tr>
        <td id="reviewingStatesHelp" class="subGroupTitle" colspan="3">${ _("Add your own statuses for the paper reviewing")}</td>
    </tr>
    <tr>
        <td class="questionContent">
            <div  style="padding-top:5px; padding-left:5px;">
                ${ _("The default statuses are: ")}<em><b>${ _("Accept, To be corrected")}</b></em>${_(" and ")}<em><b>${_("Reject")}</b></em>.
            </div>
            <div id="inPlaceEditStates"  style="padding-top: 5px;"></div>
        </td>
    </tr>
    <tr>
        <td>
            <div id="inPlaceEditStates"></div>
        </td>
    </tr>
</table>

% if ConfReview.hasPaperReviewing():
    <% display = 'table' %>
% else:
    <% display = 'none' %>
% endif
<table id="reviewingQuestionsTable" style="padding-left: 20px; padding-bottom: 20px; display:${display}">
    <tr>
        <td id="reviewingQuestionsHelp" class="subGroupTitle" colspan="3">${ _("Add the questions that the referees and the content reviewers must answer")}</td>
    </tr>
    <tr>
        <td>
            <div id="inPlaceEditContentQuestions"></div>
        </td>
    </tr>
</table>


% if ConfReview.hasPaperEditing():
    <% display = 'table' %>
% else:
    <% display = 'none' %>
% endif
<table id="editingCriteriaTable" style="padding-left: 20px; padding-bottom: 20px; display:${display}">
    <tr>
        <td id="editingCriteriaHelp" class="subGroupTitle" colspan="3">${ _("Add the questions that the layout reviewers must answer")}</td>
    </tr>
    <tr>
        <td>
            <div id="inPlaceEditLayoutQuestions"></div>
        </td>
    </tr>
</table>


% if ConfReview.hasReviewing():
    <% display = 'table' %>
% else:
    <% display = 'none' %>
% endif
<table id="defaultDueDatesTable" style="padding-left: 20px; padding-bottom: 20px; min-width: 320px; display:${display}">
    <tr>
        <td id="defaultDatesHelp" colspan="2" class="subGroupTitle" style="min-width:500px;">${ _("Default deadlines for the assessments")}</td>
    </tr>
    % if ConfReview.hasPaperReviewing():
        <% display = 'table-row' %>
    % else:
        <% display = 'none' %>
    % endif
    <tr id="refereeDefaultDateRow" style="white-space:nowrap; display: ${display}">
        <td nowrap class="deadLineCell"><span  align="left">
            ${ _("Referee Deadline")}
        </span></td>
        <td style="color: #000000;">
            <span id="inPlaceEditDefaultRefereeDueDate">
        </td>
    </tr>
    % if ConfReview.hasPaperEditing():
        <% display = 'table-row' %>
    % else:
        <% display = 'none' %>
    % endif
    <tr id="editorDefaultDateRow" style="white-space:nowrap; display: ${display}">
        <td nowrap class="deadLineCell"><span>
            ${ _("Layout Reviewer Deadline")}
        </span></td>
        <td  style="color: #000000;">
            <span id="inPlaceEditDefaultEditorDueDate">
            </span>
        </td>
        % if not ConfReview.hasPaperReviewing():
            <% display = 'table-row' %>
        % else:
            <% display = 'none' %>
        % endif
    </tr>
    % if ConfReview.hasPaperReviewing():
        <% display = 'table-row' %>
    % else:
        <% display = 'none' %>
    % endif
    <tr id="reviewerDefaultDateRow" style="white-space:nowrap;display: ${display}">
        <td nowrap class="deadLineCell"><span>
            ${ _("Content Reviewer Deadline")}
        </span></td>
        <td style="color: #000000;">
            <span id="inPlaceEditDefaultReviewerDueDate">
            </span>
        </td>
    </tr>
</table>

<table id="automaticNotification" style="padding-left: 20px; padding-bottom: 20px;">
        % if ConfReview.hasReviewing():
            <% display = 'table' %>
        % else:
            <% display = 'none' %>
        % endif
        <tr id="autoEmails" style="display:${display}">
            <td id="automaticNotificationHelp"  class="subGroupTitle" style="width:500px;">${ _("Automatic e-mails can be sent")}:
               ${inlineContextHelp(_('Here you can enable/disable automatic e-mails sending.<br/>Notifications can be send to the Reviewing Team in the next several situations<br/><ul><li>when are added/removed Reviewers for the conference</li><li>when are assinged/removed contributions to Reviewers</li><li>when authors of the contributions have been submitted materials</li></ul>Notifications can be send to the authors when their contributions had been assessed by the Reviewers.'))}
            </td>
        </tr>
        <tr id="autoEmailsPRMLabel" style="display:${display}">
           <td style="padding-top: 7px; padding-left: 7px;">
               ${ _("To the Paper Review Managers when")}:
           </td>
        </tr>
       <tr id="PRMNotif" style="white-space:nowrap; display: ${display}">
        <td style="padding-left: 20px;">
            <div>
                <span id="PRMNotifButton">
                </span>
            </div>
        </td>
       </tr>
        % if ConfReview.hasPaperReviewing():
            <% display = 'table-row' %>
        % else:
            <% display = 'none' %>
        % endif
        <tr id="autoEmailsRefereeLabel" style="display:${display}">
           <td style="padding-top: 7px; padding-left: 7px;">
               ${ _("To the Referees when")}:
           </td>
        </tr>
       <tr id="refereeNotif" style="white-space:nowrap; display: ${display}">
        <td style="padding-left: 20px;">
            <div>
                <span id="refereeNotifButton">
                </span>
            </div>
        </td>
       </tr>
       <tr id="refereeNotifForContribution" style="white-space:nowrap; display: ${display}">
        <td style="padding-left: 20px;">
            <div>
                <span id="refereeNotifForContributionButton">
                </span>
            </div>
        </td>
       </tr>
       <tr id="authorSubmittedMatRefereeNotif" style="white-space:nowrap; display: ${display}">
        <td style="padding-left: 20px;">
            <div>
                <span id="authorSubmittedMatRefereeNotifButton">
                </span>
            </div>
        </td>
       </tr>
       <tr id="editorSubmittedRefereeNotif" style="white-space:nowrap; display: ${display}">
        <td style="padding-left: 20px;">
            <div>
                <span id="editorSubmittedRefereeNotifButton">
                </span>
            </div>
        </td>
       </tr>
        <tr id="reviewerSubmittedRefereeNotif" style="white-space:nowrap; display: ${display}">
        <td style="padding-left: 20px;">
            <div>
                <span id="reviewerSubmittedRefereeNotifButton">
                </span>
            </div>
        </td>
       </tr>
        <tr id="autoEmailsContentLabel" style="display:${display}">
           <td style="padding-top: 7px; padding-left: 7px;">
               ${ _("To the Content Reviewers when")}:
           </td>
        </tr>
       <tr id="reviewerNotif" style="white-space:nowrap; display: ${display}">
        <td style="padding-left: 20px;">
            <div>
                <span id="reviewerNotifButton">
                </span>
            </div>
        </td>
       </tr>
       <tr id="reviewerNotifForContribution" style="white-space:nowrap; display: ${display}">
        <td style="padding-left: 20px;">
            <div>
                <span id="reviewerNotifForContributionButton">
                </span>
            </div>
        </td>
       </tr>
       <tr id="authorSubmittedMatReviewerNotif" style="white-space:nowrap; display: ${display}">
        <td style="padding-left: 20px;">
            <div>
                <span id="authorSubmittedMatReviewerNotifButton">
                </span>
            </div>
        </td>
       </tr>
        % if ConfReview.hasPaperEditing():
            <% display = 'table-row' %>
        % else:
            <% display = 'none' %>
        % endif
        <tr id="autoEmailsEditorLabel" style="display:${display}">
           <td style="padding-top: 7px; padding-left: 7px;">
               ${ _("To the Layout Reviewers when")}:
           </td>
        </tr>
       <tr id="editorNotif" style="white-space:nowrap; display: ${display}">
          <td style="padding-left: 20px;">
            <div>
                <span id="editorNotifButton">
                </span>
            </div>
         </td>
       </tr>
       <tr id="editorNotifForContribution" style="white-space:nowrap; display: ${display}">
          <td style="padding-left: 20px;">
            <div>
                <span id="editorNotifForContributionButton">
                </span>
            </div>
         </td>
       </tr>
       <tr id="authorSubmittedMatEditorNotif" style="white-space:nowrap; display: ${display}">
          <td style="padding-left: 20px;">
            <div>
                <span id="authorSubmittedMatEditorNotifButton">
                </span>
            </div>
         </td>
       </tr>
       % if ConfReview.hasReviewing():
            <% display = 'table-row' %>
        % else:
            <% display = 'none' %>
        % endif
        <tr id="autoEmailsAuthor" style="display:${display}">
           <td style="padding-top: 7px; padding-left: 7px;">
               ${ _("To the Author of the paper when an assessment is submitted by")}:
           </td>
        </tr>
         % if ConfReview.hasPaperReviewing():
            <% display = 'table-row' %>
        % else:
            <% display = 'none' %>
        % endif
       <tr id="refereeJudgementNotif" style="white-space:nowrap; display: ${display}">
        <td style="padding-left: 20px;">
            <div>
                <span id="refereeJudgementNotifButton">
                </span>
            </div>
        </td>
       </tr>
       <tr id="reviewerJudgementNotif" style="white-space:nowrap; display: ${display}">
        <td style="padding-left: 20px;">
            <div>
                <span id="reviewerJudgementNotifButton">
                </span>
            </div>
        </td>
       </tr>
        % if ConfReview.hasPaperEditing():
            <% display = 'table-row' %>
        % else:
            <% display = 'none' %>
        % endif
       <tr id="editorJudgementNotif" style="white-space:nowrap; display: ${display}">
          <td style="padding-left: 20px;">
            <div>
                <span id="editorJudgementNotifButton">
                </span>
            </div>
         </td>
       </tr>
</table>

% if ConfReview.hasReviewing():
    <% display = 'table' %>
% else:
    <% display = 'none' %>
% endif
<form action="${ setTemplateURL }" method="post" ENCTYPE="multipart/form-data">
<table id="templateTable" style="padding-left: 20px; padding-bottom: 20px; display:${display}">
    <tr>
        <td id="uploadTemplateHelp" class="subGroupTitle" style="width:500px;">${ _("Upload a template")}</td>
    </tr>
    <tr><td style="padding-top: 10px;">
        % if ConfReview.hasTemplates():
         <% display = 'table' %>
       % else:
         <% display = 'none' %>
       % endif
    <table id="templateListTableAll" class="infoTable" cellspacing="0" width="100%" style="display:${display}">
    <!-- here to put table for the uploaded templates info :) -->
     <thead>
        <tr>
            <td nowrap width="20%" class="tableHeader">${ _("Name")}</td>
            <td nowrap class="tableHeader">${ _("Format")}</td>
            <td nowrap class="tableHeader">${ _("Description")}</td>
            <td nowrap width="27%" class="tableHeader" style="text-align:center;">${ _("Actions")}</td>
        </tr>
        </thead>
        <tbody id="templateListTable">
        </tbody>
        </table>
        % if ConfReview.hasTemplates():
         <% display = 'none' %>
       % else:
         <% display = 'table' %>
       % endif
        <table id="NoTemplateTable" style="display:${display}">
        <tr><td style="padding-left: 7px;">
            ${ _("No templates have been uploaded yet.")}
        </td></tr>
        </table>
    </tr></td>
    <tr><a name="UploadTemplate" />
        <td style="padding-top: 5px;" ><input id='uploadTpl' type="button" value="${ _('Upload Template')}"></a>
        </td>
    </tr>
    <tr><td style="padding-bottom:15px;"></td></tr>
        <tr><td colspan="5" style="padding-top: 20px;">
            <em>${ _("Once this step is done you may want to assign the team for paper reviewing. Please click on the next tab ") }<a href="${urlHandlers.UHConfModifReviewingControl.getURL(ConfReview.getConference())}">${ _("Team")}</a>${ _(" and follow the steps")}</em>
        </td></tr>
</table>
</form>

<script type="text/javascript">

var observer = function() {

    var value = reviewingModeSelect.getCurrentValue();
    if (value == "No reviewing") {
        $E('steptitle').dom.style.display = 'none';
        $E('title').dom.style.display = 'none';
        $E('statusTable').dom.style.display = 'none';
        $E('reviewingQuestionsTable').dom.style.display = 'none';
        $E('editingCriteriaTable').dom.style.display = 'none';
        $E('defaultDueDatesTable').dom.style.display = 'none';
        $E('refereeDefaultDateRow').dom.style.display = 'none';
        $E('editorDefaultDateRow').dom.style.display = 'none';
        $E('reviewerDefaultDateRow').dom.style.display = 'none';
        $E('autoEmails').dom.style.display = 'none';
        $E('autoEmailsPRMLabel').dom.style.display = 'none';
        $E('autoEmailsRefereeLabel').dom.style.display = 'none';
        $E('autoEmailsContentLabel').dom.style.display = 'none';
        $E('autoEmailsEditorLabel').dom.style.display = 'none';
        $E('autoEmailsAuthor').dom.style.display = 'none';
        $E('PRMNotif').dom.style.display = 'none';
        $E('refereeNotif').dom.style.display = 'none';
        $E('editorNotif').dom.style.display = 'none';
        $E('reviewerNotif').dom.style.display = 'none';
        $E('refereeNotifForContribution').dom.style.display = 'none';
        $E('editorNotifForContribution').dom.style.display = 'none';
        $E('reviewerNotifForContribution').dom.style.display = 'none';
        $E('refereeJudgementNotif').dom.style.display = 'none';
        $E('editorJudgementNotif').dom.style.display = 'none';
        $E('reviewerJudgementNotif').dom.style.display = 'none';
        $E('authorSubmittedMatRefereeNotif').dom.style.display = 'none';
        $E('authorSubmittedMatEditorNotif').dom.style.display = 'none';
        $E('authorSubmittedMatReviewerNotif').dom.style.display = 'none';
        $E('editorSubmittedRefereeNotif').dom.style.display = 'none';
        $E('reviewerSubmittedRefereeNotif').dom.style.display = 'none';

        $E('templateTable').dom.style.display = 'none';
    }
    if (value == "Content reviewing") {
        $E('steptitle').dom.style.display = '';
        $E('title').set('${ _("content reviewing team")}');
        $E('title').dom.style.display = '';
        $E('statusTable').dom.style.display = '';
        $E('reviewingQuestionsTable').dom.style.display = '';
        $E('editingCriteriaTable').dom.style.display = 'none';
        $E('defaultDueDatesTable').dom.style.display = '';
        $E('refereeDefaultDateRow').dom.style.display = '';
        $E('editorDefaultDateRow').dom.style.display = 'none';
        $E('reviewerDefaultDateRow').dom.style.display = '';
        $E('autoEmails').dom.style.display = '';
        $E('autoEmailsPRMLabel').dom.style.display = '';
        $E('PRMNotif').dom.style.display = '';
        $E('autoEmailsRefereeLabel').dom.style.display = '';
        $E('autoEmailsContentLabel').dom.style.display = '';
        $E('autoEmailsEditorLabel').dom.style.display = 'none';
        $E('autoEmailsAuthor').dom.style.display = '';
        $E('refereeNotif').dom.style.display = '';
        $E('editorNotif').dom.style.display = 'none';
        $E('reviewerNotif').dom.style.display = '';
        $E('refereeNotifForContribution').dom.style.display = '';
        $E('editorNotifForContribution').dom.style.display = 'none';
        $E('reviewerNotifForContribution').dom.style.display = '';
        $E('refereeJudgementNotif').dom.style.display = '';
        $E('editorJudgementNotif').dom.style.display = 'none';
        $E('reviewerJudgementNotif').dom.style.display = '';
        $E('authorSubmittedMatRefereeNotif').dom.style.display = '';
        $E('authorSubmittedMatEditorNotif').dom.style.display = 'none';
        $E('authorSubmittedMatReviewerNotif').dom.style.display = '';
        $E('editorSubmittedRefereeNotif').dom.style.display = 'none';
        $E('reviewerSubmittedRefereeNotif').dom.style.display = '';
        $E('templateTable').dom.style.display = '';

        showReviewingStates();
        showReviewingQuestions();
        showDefaultReviewerDate();
        showDefaultRefereeDate();
    }
    if (value == "Layout reviewing") {
        $E('steptitle').dom.style.display = '';
        $E('title').dom.style.display = '';
        $E('title').set('${ _("layout reviewing team")}');
        $E('statusTable').dom.style.display = 'none';
        $E('reviewingQuestionsTable').dom.style.display = 'none';
        $E('editingCriteriaTable').dom.style.display = '';
        $E('defaultDueDatesTable').dom.style.display = '';
        $E('refereeDefaultDateRow').dom.style.display = 'none';
        $E('editorDefaultDateRow').dom.style.display = '';
        $E('reviewerDefaultDateRow').dom.style.display = 'none';
        $E('autoEmails').dom.style.display = '';
        $E('autoEmailsPRMLabel').dom.style.display = '';
        $E('PRMNotif').dom.style.display = '';
        $E('autoEmailsRefereeLabel').dom.style.display = 'none';
        $E('autoEmailsContentLabel').dom.style.display = 'none';
        $E('autoEmailsEditorLabel').dom.style.display = '';
        $E('autoEmailsAuthor').dom.style.display = '';
        $E('refereeNotif').dom.style.display = 'none';
        $E('editorNotif').dom.style.display = '';
        $E('reviewerNotif').dom.style.display = 'none';
        $E('refereeNotifForContribution').dom.style.display = 'none';
        $E('editorNotifForContribution').dom.style.display = '';
        $E('reviewerNotifForContribution').dom.style.display = 'none';
        $E('refereeJudgementNotif').dom.style.display = 'none';
        $E('editorJudgementNotif').dom.style.display = '';
        $E('reviewerJudgementNotif').dom.style.display = 'none';
        $E('authorSubmittedMatRefereeNotif').dom.style.display = 'none';
        $E('authorSubmittedMatEditorNotif').dom.style.display = '';
        $E('authorSubmittedMatReviewerNotif').dom.style.display = 'none';
        $E('editorSubmittedRefereeNotif').dom.style.display = 'none';
        $E('reviewerSubmittedRefereeNotif').dom.style.display = 'none';
        $E('templateTable').dom.style.display = '';

        showEditingCriteria();
        showDefaultEditorDate();
    }
    if (value == "Content and layout reviewing") {
        $E('steptitle').dom.style.display = '';
        $E('title').set('${ _("content and layout reviewing team")}');
        $E('title').dom.style.display = '';
        $E('statusTable').dom.style.display = '';
        $E('reviewingQuestionsTable').dom.style.display = '';
        $E('editingCriteriaTable').dom.style.display = '';
        $E('defaultDueDatesTable').dom.style.display = '';
        $E('refereeDefaultDateRow').dom.style.display = '';
        $E('editorDefaultDateRow').dom.style.display = '';
        $E('reviewerDefaultDateRow').dom.style.display = '';
        $E('autoEmailsRefereeLabel').dom.style.display = '';
        $E('autoEmailsContentLabel').dom.style.display = '';
        $E('autoEmailsEditorLabel').dom.style.display = '';
        $E('autoEmailsAuthor').dom.style.display = '';
        $E('autoEmails').dom.style.display = '';
        $E('autoEmailsPRMLabel').dom.style.display = '';
        $E('PRMNotif').dom.style.display = '';
        $E('refereeNotif').dom.style.display = '';
        $E('editorNotif').dom.style.display = '';
        $E('reviewerNotif').dom.style.display = '';
        $E('refereeNotifForContribution').dom.style.display = '';
        $E('editorNotifForContribution').dom.style.display = '';
        $E('reviewerNotifForContribution').dom.style.display = '';
        $E('refereeJudgementNotif').dom.style.display = '';
        $E('editorJudgementNotif').dom.style.display = '';
        $E('reviewerJudgementNotif').dom.style.display = '';
        $E('authorSubmittedMatRefereeNotif').dom.style.display = '';
        $E('authorSubmittedMatEditorNotif').dom.style.display = '';
        $E('authorSubmittedMatReviewerNotif').dom.style.display = '';
        $E('editorSubmittedRefereeNotif').dom.style.display = '';
        $E('reviewerSubmittedRefereeNotif').dom.style.display = '';
        $E('templateTable').dom.style.display = '';

        showReviewingStates();
        showReviewingQuestions();
        showDefaultReviewerDate();
        showDefaultRefereeDate();
        showEditingCriteria();
        showDefaultEditorDate();
    }
}

var reviewingModeSelect = new SelectEditWidget('reviewing.conference.changeReviewingMode',
        {conference: '${ ConfReview.getConference().getId() }'}, ${ reviewingModesDict }
        , "${ ConfReview.getReviewingMode() }", observer);
$E('inPlaceEditReviewingMode').set(reviewingModeSelect.draw());

var showReviewingStates = function() {
    $E('inPlaceEditStates').set(new ManageListOfElements({'get':'reviewing.paperReviewing.getStatuses',
        'add':'reviewing.paperReviewing.addStatus', 'remove':'reviewing.paperReviewing.removeStatus',
        'edit': 'reviewing.paperReviewing.editStatus'},
        {conference: '${ ConfReview.getConference().getId() }'},'status', 'statusComponent', false).draw());
}

var showReviewingQuestions = function() {
    $E('inPlaceEditContentQuestions').set(new ManageListOfElements({'get':'reviewing.paperReviewing.getContentQuestions',
        'add':'reviewing.paperReviewing.addContentQuestion', 'remove':'reviewing.paperReviewing.removeContentQuestion',
        'edit': 'reviewing.paperReviewing.editContentQuestion'},
        {conference: '${ ConfReview.getConference().getId() }'},'question', 'contentReviewerQuestion', false).draw());
}

var showEditingCriteria = function() {
    $E('inPlaceEditLayoutQuestions').set(new ManageListOfElements({'get':'reviewing.paperReviewing.getLayoutQuestions',
        'add':'reviewing.paperReviewing.addLayoutQuestion', 'remove':'reviewing.paperReviewing.removeLayoutQuestion',
        'edit': 'reviewing.paperReviewing.editLayoutQuestion'},
        {conference: '${ ConfReview.getConference().getId() }'},'question', 'layoutReviewerQuestion', false).draw());
}



var showDefaultRefereeDate = function() {
    $('#inPlaceEditDefaultRefereeDueDate').html(new DateDeadlineWidget('reviewing.conference.changeDefaultDueDate',
            {conference: '${ ConfReview.getConference().getId() }',
             dueDateToChange: 'Referee'}, ${ConfReview.getAdjustedDefaultRefereeDueDate() | n,j}, ${ConfReview.getConference().getNumberOfContributions() > 0 | n,j}).draw().dom);
}

var showDefaultEditorDate = function() {
    $('#inPlaceEditDefaultEditorDueDate').html(new DateDeadlineWidget('reviewing.conference.changeDefaultDueDate',
            {conference: '${ ConfReview.getConference().getId() }',
             dueDateToChange: 'Editor'}, ${ConfReview.getAdjustedDefaultEditorDueDate() | n,j}, ${ConfReview.getConference().getNumberOfContributions() > 0 | n,j}).draw().dom);
}

var showDefaultReviewerDate = function() {
    $('#inPlaceEditDefaultReviewerDueDate').html(new DateDeadlineWidget('reviewing.conference.changeDefaultDueDate',
        {conference: '${ ConfReview.getConference().getId() }',
    dueDateToChange: 'Reviewer'}, ${ConfReview.getAdjustedDefaultReviewerDueDate() | n,j}, ${ConfReview.getConference().getNumberOfContributions() > 0 | n,j}).draw().dom);
}


var TemplateList = function(){
            <% keys = ConfReview.getTemplates().keys() %>
            % for k in keys:
                <% t = ConfReview.getTemplates()[k] %>
                    var row = Html.tr({id:'TemplateRow_'+'${t.getId()}', className:'infoTR'});

                    var deleteTpl = function(selectedRow) {
                        var params = {conference: ${ ConfReview.getConference().getId() },
                                      templateId: selectedRow.dom.id.split("TemplateRow_")[1]};
                        var name = $E('TemplateSpanName_' + selectedRow.dom.id.split("TemplateRow_")[1]).dom.innerHTML;

                        new ConfirmPopup($T("Delete template"),$T("Are you sure you want to delete {0}?").format(name), function(confirmed) {
                            if(confirmed) {
                                var killProgress = IndicoUI.Dialogs.Util.progress($T('Removing...'));
                                jsonRpc(Indico.Urls.JsonRpcService,
                                    'reviewing.conference.deleteTemplate',
                                    params,
                                    function(response,error) {
                                            if (exists(error)) {
                                                killProgress();
                                                IndicoUtil.errorReport(error);
                                            } else {
                                                killProgress();
                                                $E('templateListTable').remove(selectedRow);
                                                tablerows = document.getElementById('templateListTableAll').rows.length;
                                                if(tablerows == '1'){
                                                    $E('NoTemplateTable').dom.style.display = '';
                                                    $E('templateListTableAll').dom.style.display = 'none';}
                                            }
                                        });
                            }
                        }).open();
                    };

                    var nameSpan = Html.span({id:'TemplateSpanName_'+'${ t.getId()}'}, '${ t.getName()}');
                    var cellName = Html.td({id:'TemplateName_'+'${ t.getId()}', className:'content'}, nameSpan);

                    var cellFormat = Html.td({id:'TemplateName_'+'${ t.getId()}', className:'content'}, '${ t.getFormat()}');
                    var cellDescription = Html.td({id:'TemplateName_'+'${ t.getId()}', className:'content'}, ${t.getDescription() | n,j});
                    var downloadURL = "${ urlHandlers.UHDownloadContributionTemplate.getURL(t) }";
                    var downloadSpan = Html.a({href: downloadURL}, "Download");
                    var barSpan = Html.span({className:'horizontalSeparator'}, "|");
                    var removeSpan = Html.span({className:'link'}, "Remove");
                    var cellActions = Html.td({className:'content', style:{textAlign: 'right'}});
                    cellActions.append(downloadSpan);
                    cellActions.append(barSpan);
                    cellActions.append(removeSpan);
                    row.append(cellName);
                    row.append(cellFormat);
                    row.append(cellDescription);
                    row.append(cellActions);
                    removeSpan.observeClick(function(event){
                        var selectedRow = $E('TemplateRow_'+'${t.getId()}');
                        deleteTpl(selectedRow);
                    });


                    $E('templateListTable').append(row);
             % endfor

          }


$('#PRMNotifButton').html(new SwitchOptionButton('reviewing.conference.PRMEmailNotif',
                                            {conference: '${ ConfReview.getConference().getId() }',
                                            AutoEmailsToChange: 'PRM'},
                                            $T('are added to/removed from the conference'),
                                            $T("Saved"),
                                            null,
                                            false
).draw());

$('#refereeNotifButton').html(new SwitchOptionButton('reviewing.conference.RefereeEmailNotif',
                                            {conference: '${ ConfReview.getConference().getId() }',
                                            AutoEmailsToChange: 'Referee'},
                                            $T('are added to/removed from the conference'),
                                            $T("Saved"),
                                            null,
                                            false
).draw());
$('#reviewerNotifButton').html(new SwitchOptionButton('reviewing.conference.ReviewerEmailNotif',
                                            {conference: '${ ConfReview.getConference().getId() }',
                                            AutoEmailsToChange: 'Reviewer'},
                                            $T('are added to/removed from the conference'),
                                            $T("Saved"),
                                            null,
                                            false
).draw());
$('#editorNotifButton').html(new SwitchOptionButton('reviewing.conference.EditorEmailNotif',
                                            {conference: '${ ConfReview.getConference().getId() }',
                                            AutoEmailsToChange: 'Editor'},
                                            $T('are added to/removed from the conference'),
                                            $T("Saved"),
                                            null,
                                            false
).draw());
$('#refereeNotifForContributionButton').html(new SwitchOptionButton('reviewing.conference.RefereeEmailNotifForContribution',
                                            {conference: '${ ConfReview.getConference().getId() }',
                                            AutoEmailsToChange: 'Referee'},
                                            $T('have been assigned to/unassigned from contributions'),
                                            $T("Saved"),
                                            null,
                                            false
).draw());
$('#reviewerNotifForContributionButton').html(new SwitchOptionButton('reviewing.conference.ReviewerEmailNotifForContribution',
                                            {conference: '${ ConfReview.getConference().getId() }',
                                            AutoEmailsToChange: 'Reviewer'},
                                            $T('have been assigned to/unassigned from contributions'),
                                            $T("Saved"),
                                            null,
                                            false
).draw());
$('#editorNotifForContributionButton').html(new SwitchOptionButton('reviewing.conference.EditorEmailNotifForContribution',
                                            {conference: '${ ConfReview.getConference().getId() }',
                                            AutoEmailsToChange: 'Editor'},
                                            $T('have been assigned to/unassigned from contributions'),
                                            $T("Saved"),
                                            null,
                                            false
).draw());
$('#refereeJudgementNotifButton').html(new SwitchOptionButton('reviewing.conference.RefereeEmailJudgementNotif',
                                            {conference: '${ ConfReview.getConference().getId() }',
                                            AutoEmailsToChange: 'Referee'},
                                            $T('Referee (for any assessment)'),
                                            $T("Saved"),
                                            null,
                                            false
).draw());
$('#reviewerJudgementNotifButton').html(new SwitchOptionButton('reviewing.conference.ReviewerEmailJudgementNotif',
                                            {conference: '${ ConfReview.getConference().getId() }',
                                            AutoEmailsToChange: 'Reviewer'},
                                            $T('Content Reviewer (for assessments that imply corrections)'),
                                            $T("Saved"),
                                            null,
                                            false
).draw());
$('#editorJudgementNotifButton').html(new SwitchOptionButton('reviewing.conference.EditorEmailJudgementNotif',
                                            {conference: '${ ConfReview.getConference().getId() }',
                                            AutoEmailsToChange: 'Editor'},
                                            $T('Layout Reviewer') + ${ _("' (for assessments that imply corrections)'") if ConferencePaperReview.reviewingModes[choice]!=ConferencePaperReview.reviewingModes[3] else "''"},
                                            $T("Saved"),
                                            null,
                                            false
).draw());
$('#authorSubmittedMatRefereeNotifButton').html(new SwitchOptionButton('reviewing.conference.AuthorSubmittedMatRefereeNotif',
                                            {conference: '${ ConfReview.getConference().getId() }',
                                            AutoEmailsToChange: 'Referee'},
                                            $T('the author submits a paper'),
                                            $T("Saved"),
                                            null,
                                            false
).draw());
$('#authorSubmittedMatReviewerNotifButton').html(new SwitchOptionButton('reviewing.conference.AuthorSubmittedMatEditorNotif',
                                            {conference: '${ ConfReview.getConference().getId() }',
                                            AutoEmailsToChange: 'Reviewer'},
                                            $T('the author submits a paper'),
                                            $T("Saved"),
                                            null,
                                            false
).draw());
$('#authorSubmittedMatEditorNotifButton').html(new SwitchOptionButton('reviewing.conference.AuthorSubmittedMatReviewerNotif',
                                            {conference: '${ ConfReview.getConference().getId() }',
                                            AutoEmailsToChange: 'Editor'},
                                            $T('the author submits a paper'),
                                            $T("Saved"),
                                            null,
                                            false
).draw());
$('#editorSubmittedRefereeNotifButton').html(new SwitchOptionButton('reviewing.conference.EditorSubmittedRefereeNotif',
        {conference: '${ ConfReview.getConference().getId() }',
        AutoEmailsToChange: 'Referee'},
        $T('a layout reviewer submits an assessment'),
        $T("Saved"),
        null,
        false
).draw());
$('#reviewerSubmittedRefereeNotifButton').html(new SwitchOptionButton('reviewing.conference.ReviewerSubmittedRefereeNotif',
        {conference: '${ ConfReview.getConference().getId() }',
    AutoEmailsToChange: 'Referee'},
    $T('a content reviewer submits an assessment'),
    $T("Saved"),
    null,
    false
).draw());

% if ConfReview.hasReviewing():
    TemplateList();

    $E('uploadTpl').observeClick(function(){ var popup = new UploadTemplateDialog( 'Upload Template',
        {conference: '${ ConfReview.getConference().getId() }'}, '350px', '30px',
        ${ jsonEncode(Template.formats) }, '${ urlHandlers.UHSetTemplate.getURL(ConfReview.getConference()) }',
        function(value) {
            $E('NoTemplateTable').dom.style.display = 'none';
            $E('templateListTableAll').dom.style.display = '';

            var row = Html.tr({id:'TemplateRow_' + value.id, className:'infoTR'});
            var params = {conference: '${ ConfReview.getConference().getId() }',templateId: value.id}
            var deleteTemplate = function() {
                new ConfirmPopup($T("Delete template"),$T("Are you sure you want to delete {0}?").format(name), function(confirmed) {
                    if(confirmed) {
                        var killProgress = IndicoUI.Dialogs.Util.progress($T('Removing...'));
                        jsonRpc(Indico.Urls.JsonRpcService,
                        'reviewing.conference.deleteTemplate',
                        params,
                            function(response,error) {
                                if (exists(error)) {
                                    killProgress();
                                    IndicoUtil.errorReport(error);
                                } else {
                                    killProgress();
                                    $E('templateListTable').remove(row);
                                    tablerows = document.getElementById('templateListTableAll').rows.length;
                                    if(tablerows == '1'){
                                        $E('NoTemplateTable').dom.style.display = '';
                                        $E('templateListTableAll').dom.style.display = 'none';}
                                }
                            });
                    }
                }).open();
            };

            var nameSpan = Html.span({}, value.name);
            var cellName = Html.td({id:'TemplateName_'+ value.id, className:'content'}, nameSpan);
            var cellFormat = Html.td({id:'TemplateName_'+ value.id, className:'content'}, value.format);
            var cellDescription = Html.td({id:'TemplateName_'+ value.id, className:'content'}, value.description);
            var downloadURL = build_url(${ urlHandlers.UHDownloadContributionTemplate.getURL().js_router | j,n }, {
                reviewingTemplateId: value.id,
                confId: ${ConfReview.getConference().getId()}
            });
            var downloadSpan = Html.a({href: downloadURL}, "Download");
            var barSpan = Html.span({className:'horizontalSeparator'}, "|");
            var removeSpan = Html.span({className:'link'}, "Remove");
            var cellActions = Html.td({className:'content', style:{textAlign: 'right'}});
            cellActions.append(downloadSpan);
            cellActions.append(barSpan);
            cellActions.append(removeSpan);
            row.append(cellName);
            row.append(cellFormat);
            row.append(cellDescription);
            row.append(cellActions);

            removeSpan.observeClick(deleteTemplate);

            return $E('templateListTable').append(row);

            }); popup.open();
            }
            );
% endif
% if ConfReview.hasPaperReviewing():
    showReviewingStates();
    showReviewingQuestions();
    showDefaultReviewerDate();
    showDefaultRefereeDate();
% endif
% if ConfReview.hasPaperEditing():
    showEditingCriteria();
    showDefaultEditorDate();
% endif

</script>
