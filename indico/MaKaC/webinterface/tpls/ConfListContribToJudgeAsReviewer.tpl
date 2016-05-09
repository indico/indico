<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.common.timezoneUtils import nowutc %>

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
        <% review_manager = Conference.getReviewManager(c) %>
        <tr valign="top" onmouseover="this.style.backgroundColor='#ECECEC'" onmouseout="this.style.backgroundColor='transparent'">
            <td style="padding-right:5px;padding-left:5px;">${ c.id }</td>
            % if not review_manager.getLastReview().getRefereeJudgement().isSubmitted() and review_manager.getLastReview().isAuthorSubmitted():
                    <td style="padding-right:5px;padding-left:5px;">
                        <a href="${ url_for('event_mgmt.contributionGiveAdvice', c) }">${ c.title }</a>
                    </td>
                % endif
                % if review_manager.getLastReview().getRefereeJudgement().isSubmitted():
                    <td style="padding-right:5px;padding-left:5px;">
                        <span onmouseover=" IndicoUI.Widgets.Generic.tooltip(this, event, 'Final assessment already given by the referee')">${ c.title }</span>
                    </td>
                % endif
                % if not review_manager.getLastReview().isAuthorSubmitted():
                       <td style="padding-right:5px;padding-left:5px;">
                                <span onmouseover=" IndicoUI.Widgets.Generic.tooltip(this, event, 'You must wait for the author to submit the materials<br/> before you assess the contribution.')">
                                   ${ c.title }
                                </span>
                       </td>
                   % endif
            <td style="padding-right:5px;padding-left:5px;">
                ${_("Review {0}").format(len(review_manager.getVersioning()))}
            </td>
            <td style="padding-right:5px;padding-left:5px;">
                % if review_manager.getLastReview().hasGivenAdvice(User):
                    <% advice = review_manager.getLastReview().getAdviceFrom(User).getJudgement() %>
                    <%
                        if advice == 'Accept':
                            advice_color = '#118822'
                        elif advice == 'Reject':
                            advice_color = '#881122'
                        else:
                            advice_color = 'orange'
                    %>
                    <span style="color:${advice_color}">${ _("Advice  given: ") + advice }</span>
                % elif not review_manager.getLastReview().isAuthorSubmitted():
                    % if len(review_manager.getVersioning()) > 1:
                        <span style="color:orange;">${ _("Author has yet to re-submit paper") }</span>
                    % else:
                        <span>${ _("Paper not yet submitted")}</span>
                    % endif
                % else:
                    % if len(review_manager.getVersioning()) > 1:
                        <span style="color:#D18700;">
                            ${ _("Author has re-submitted paper")}
                        </span><br/>
                    % endif
                    <% referee_did = review_manager.getLastReview().getRefereeJudgement().isSubmitted() %>
                    <span ${ "style='font-weight: bold;'" if not referee_did else "" }>
                    ${ _("Advice not yet given")}
                    </span>
                    % if referee_did:
                    <span style="color:#3F4C6B;">${ _("but Referee already assessed contribution")}</span>
                    % endif
                % endif
            </td>
            <td style="padding-right:5px;padding-left:5px;">
            <% date = review_manager.getLastReview().getAdjustedReviewerDueDate() %>
            % if date is None:
                ${ _("Deadline not set.")}
            % else:
                <span>${ date.strftime(dueDateFormat) }</span>
            % endif
            </td>
        </tr>
    % endfor

</table>
% endif
% if not ConfReview.getReviewedContributions(User):
<p style="padding-left: 25px;"><font color="gray">${ _("No contributions have so far been assigned to you for judgement.")}</font></p>
% endif
