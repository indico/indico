<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.common.timezoneUtils import nowutc %>
<% from MaKaC.conference import ContribStatusNone %>

<% dueDateFormat = "%a %d %b %Y" %>

% if ConfReview.getReviewedContributions(User):

<table class="Revtab" width="90%" cellspacing="0" cellpadding="10px" align="center" border="0" style="padding-left:2px; padding-top: 10px">
    <tr>
        <td nowrap class="groupTitle" colspan=5>${ _("Give advice on content of the paper")}</td>
    </tr>
    <tr>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;">${ _("Id")}</td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;">${ _("Title")}</td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;">${ _("Review #")}</td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;">${ _("State")}</td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;">${ _("Deadline")}</td>
    </tr>

    % for c in ConfReview.getReviewedContributions(User):
        % if not isinstance(c.getStatus(), ContribStatusNone):
        <tr valign="top" onmouseover="this.style.backgroundColor='#ECECEC'" onmouseout="this.style.backgroundColor='transparent'">
            <td style="padding-right:5px;padding-left:5px;">${ c.getId() }</td>
            % if not c.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted() and c.getReviewManager().getLastReview().isAuthorSubmitted():
                    <td style="padding-right:5px;padding-left:5px;">
                        <a href="${ urlHandlers.UHContributionGiveAdvice.getURL(c) }">${ c.getTitle() }</a>
                    </td>
                % endif
                % if c.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted():
                    <td style="padding-right:5px;padding-left:5px;">
                        <span onmouseover=" IndicoUI.Widgets.Generic.tooltip(this, event, 'Final assessment already given by the referee')">${ c.getTitle() }</span>
                    </td>
                % endif
                % if not c.getReviewManager().getLastReview().isAuthorSubmitted():
                       <td style="padding-right:5px;padding-left:5px;">
                                <span onmouseover=" IndicoUI.Widgets.Generic.tooltip(this, event, 'You must wait for the author to submit the materials<br/> before you assess the contribution.')">
                                   ${ c.getTitle() }
                                </span>
                       </td>
                   % endif
            <td style="padding-right:5px;padding-left:5px;">
                ${_("Review {0}").format(len(c.getReviewManager().getVersioning()))}
            </td>
            <td style="padding-right:5px;padding-left:5px;">
                % if c.getReviewManager().getLastReview().hasGivenAdvice(User):
                    <% advice = c.getReviewManager().getLastReview().getAdviceFrom(User).getJudgement() %>
                    <%
                        if advice == 'Accept':
                            advice_color = '#118822'
                        elif advice == 'Reject':
                            advice_color = '#881122'
                        else:
                            advice_color = 'orange'
                    %>
                    <span style="color:${advice_color}">${ _("Advice  given: ") + advice }</span>
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
                    <% referee_did = c.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted() %>
                    <span ${ "style='font-weight: bold;'" if not referee_did else "" }>
                    ${ _("Advice not yet given")}
                    </span>
                    % if referee_did:
                    <span style="color:#3F4C6B;">${ _("but Referee already assessed contribution")}</span>
                    % endif
                % endif
            </td>
            <td style="padding-right:5px;padding-left:5px;">
            <% date = c.getReviewManager().getLastReview().getAdjustedReviewerDueDate() %>
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
% endif
% if not ConfReview.getReviewedContributions(User):
<p style="padding-left: 25px;"><font color="gray">${ _("No contributions have so far been assigned to you for judgement.")}</font></p>
% endif
