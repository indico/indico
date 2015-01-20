<% import MaKaC.webinterface.urlHandlers as urlHandlers %>

% if not ConfReview.hasReviewing():
<p style="padding-left: 25px; color:gray;">${ _("Type of reviewing has not been chosen yet. You can choose it from Paper Reviewing ")}<a href="${urlHandlers.UHConfModifReviewingPaperSetup.getURL(ConfReview.getConference())}">${ _("Setup.")}</a></p>
% elif ConfReview.getAllUserCompetences() == []:
<table align="left" style="color:gray; font-style:italic; padding-left:10px;"><tr><td>${ _("The Reviewing Team has not been assigned yet.")}</td></tr></table>
%else:
<table class="Revtab" width="90%" cellspacing="0" align="left" border="0" style="padding-left:2px; padding-top: 10px;">
    <tr>
        <td nowrap class="groupTitle" colspan=5>
            ${ _("Team competences")}
            <span id="competencesHelp"></span>
        </td>
    </tr>
    <tr>
        <td colspan="4">
            <div style="padding:5px; color:gray;">
                <span class="italic">${ _("To define competences for each user could help you to choose better the user when you assign contributions.")}</span>
            </div>
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF; padding-top: 10px; padding-bottom: 10px;">${ _("Id")}</td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF; padding-top: 10px; padding-bottom: 10px;">${ _("Name")}</td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF; padding-top: 10px; padding-bottom: 10px;">${ _("Responsibilities")}</td>
        <td colspan=2 nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF; padding-top: 10px; padding-bottom: 10px;">${ _("Competences")}</td>
    </tr>


    % for user, competences in ConfReview.getAllUserCompetences():
    % if ConfReview.getUserReviewingRoles(user):
    % if ConfReview.isPaperReviewManager(user) or ConfReview.isReferee(user) or ConfReview.isEditor(user) or ConfReview.isReviewer(user):
        <tr valign="top">
            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF; padding-top: 5px;">${ user.getId() }</td>
            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF; padding-top: 5px;">${ user.getFullName()}</td>
            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF; padding-top: 5px;">
                ${ ", ".join(ConfReview.getUserReviewingRoles(user)) }
            </td>
            <td  style="padding-top: 5px;">
                <span id="competences_${ user.getId() }"></span>
            </td>
        </tr>
    % endif
    % endif
    % endfor
    <tr><td colspan=5 style="padding-top: 15px;">
       <em>${ _("Once this step is done you may want to assign papers to review. Please click on the next tab ") }<a href="${urlHandlers.UHConfModifReviewingAssignContributionsList.getURL(ConfReview.getConference())}">${ _("Assign Papers")}</a>${ _(" to continue the process.")}</em>
   </td></tr>
</table>

<script type="text/javascript">

var keyWordfieldList = new Array()
% for user, competences in ConfReview.getAllUserCompetences():
 % if ConfReview.isPaperReviewManager(user) or ConfReview.isReferee(user) or ConfReview.isEditor(user) or ConfReview.isReviewer(user):
    new IndicoUI.Widgets.Generic.keywordField(
        $E('competences_${ user.getId() }'),
        'oneLineListItem',
        'reviewing.conference.changeCompetences',
        {
            conference: '${ Conference.getId() }',
            user: '${ user.getId() }'
        }
    );
 % endif
% endfor
</script>
% endif
