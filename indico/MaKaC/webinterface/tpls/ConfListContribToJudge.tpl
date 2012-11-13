<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.common.timezoneUtils import nowutc %>
<% from MaKaC.conference import ContribStatusNone %>

<% dueDateFormat = "%a %d %b %Y" %>

% if ConfReview.getJudgedContributions(User):
<table class="Revtab" width="90%" cellspacing="0" cellpadding="10px" align="center" border="0" style="padding-left:2px; padding-top: 10px">
    <tr>
        <td nowrap class="groupTitle" colspan=5 style="">${ _("Contributions to judge as Referee")}</td>
    </tr>
    <tr>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;">${ _("Id")}</td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;">${ _("Title")}</td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;">${ _("Review #")}</td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;">${ _("State")}</td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;">${ _("Deadline")}</td>
    </tr>

    % for c in ConfReview.getJudgedContributions(User):
        % if not isinstance(c.getStatus(), ContribStatusNone):
        <tr valign="top" onmouseover="this.style.backgroundColor='#ECECEC'" onmouseout="this.style.backgroundColor='transparent'">
            <td style="padding-right:5px;padding-left:5px;">${ c.getId() }</td>
            <td style="padding-right:5px;padding-left:5px;"><a href="${ urlHandlers.UHContributionModifReviewing.getURL(c) }">${ c.getTitle() }</a></td>
            <td style="padding-right:5px;padding-left:5px;">
                ${_("Review {0}").format(len(c.getReviewManager().getVersioning()))}
            </td>
            <td style="padding-right:5px;padding-left:5px;">
            % if c.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted():
                <% assessment = c.getReviewManager().getLastReview().getRefereeJudgement().getJudgement() %>
                <%
                    if assessment == 'Accept':
                        assessment_color = '#118822'
                    elif assessment == 'Reject':
                        assessment_color = '#881122'
                    else:
                        assessment_color = 'orange'
                %>
                <span style="color:${assessment_color}">${ _("Assessed: ") + assessment }</span>
            % elif not c.getReviewManager().getLastReview().isAuthorSubmitted():
                % if len(c.getReviewManager().getVersioning()) > 1:
                    <span style="color:orange;">${ _("Author has yet to re-submit paper") }</span>
                % else:
                    <span>${ _("Paper not yet submitted")}</span>
                % endif
            % else:
                % if len(c.getReviewManager().getVersioning()) > 1:
                    <span style="color:#D18700;">
                        ${ _("Author has re-submitted paper")}
                    </span><br/>
                % endif
                <span style="font-weight: bold;">
                    ${ _("Referee has not yet given an assessment")}
                    <br>
                </span>
                <ul style="margin:0px;padding-left:30px">
                % for status in (c.getReviewManager().getLastReview().getReviewingStatus(forAuthor = False)):
                    <li>${status}</li>
                % endfor
                </ul>
            % endif
            </td>
            <td style="padding-right:5px;padding-left:5px;" onmouseover="this.style.borderColor='#ECECEC'" onmouseout="this.style.borderColor='transparent'">
                <% date = c.getReviewManager().getLastReview().getAdjustedRefereeDueDate() %>
                % if date is None:
                    ${ _("Deadline not set.")}
                % else:
                    <span>${ date.strftime(dueDateFormat) }</span>
                % endif
            </td>
        </tr>
        % endif
    % endfor
</table>
<br>
% endif
% if not ConfReview.getJudgedContributions(User):
<p style="padding-left: 25px;"><font color="gray">${ _("No contributions have so far been assigned to you for judgement.")}</font></p>
% endif
