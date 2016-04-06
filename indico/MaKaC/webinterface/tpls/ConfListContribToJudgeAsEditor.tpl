<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.common.timezoneUtils import nowutc %>
<% from MaKaC.conference import ContribStatusNone %>
<% from MaKaC.paperReviewing import ConferencePaperReview as CPR %>

<% dueDateFormat = "%a %d %b %Y" %>

% if ConfReview.getEditedContributions(User):
<table class="Revtab" width="90%" cellspacing="0" cellpadding='10px' align="center" border="0" style="padding-left:2px; padding-top: 10px">
    <tr>
        <td nowrap class="groupTitle" colspan=5>${ _("Judge editing of the contribution")}</td>
    </tr>
    <tr>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;">${ _("Id")}</td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;">${ _("Title")}</td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;">${ _("Review #")}</td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;">${ _("State")}</td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;padding-top:10px; padding-bottom:10px;">${ _("Deadline")}</td>
    </tr>

    % for c in ConfReview.getEditedContributions(User):
        <% review_manager = ConfReview.getReviewManager(c) %>
        <tr valign="top" onmouseover="this.style.backgroundColor='#ECECEC'" onmouseout="this.style.backgroundColor='transparent'">
            <td style="padding-right:5px;padding-left:5px;">${ c.id }</td>
            % if review_manager.getLastReview().isAuthorSubmitted():
                % if ConfReview.getChoice() == CPR.LAYOUT_REVIEWING or not review_manager.getLastReview().getRefereeJudgement().isSubmitted():
                        <td style="padding-right:5px;padding-left:5px;">
                            <a href="${ url_for('event_mgmt.contributionEditingJudgement', c) }">${ c.title }</a>
                        </td>
                % endif
                % if ConfReview.getChoice() == CPR.CONTENT_AND_LAYOUT_REVIEWING and review_manager.getLastReview().getRefereeJudgement().isSubmitted() :
                       <td style="padding-right:5px;padding-left:5px;">
                                <span onmouseover=" IndicoUI.Widgets.Generic.tooltip(this, event, 'Assessment already given by the referee')">
                                   ${ c.title }
                                </span>
                        </td>
                % endif
            % else:
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
                % if review_manager.getLastReview().getEditorJudgement().isSubmitted():
                    <% assessment = review_manager.getLastReview().getEditorJudgement().getJudgement() %>
                    <%
                        if assessment == 'Accept':
                            assessment_color = '#118822'
                        elif assessment == 'Reject':
                            assessment_color = '#881122'
                        else:
                            assessment_color = 'orange'
                    %>
                    <span style="color:${assessment_color}">${ _("Layout assessment given: ") + assessment }</span>
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
                        ${ _("Layout assessment not yet given")}
                    </span>
                    % if referee_did and ConfReview.getChoice() == CPR.CONTENT_AND_LAYOUT_REVIEWING:
                    <span style="color:#3F4C6B;">${ _("but Referee already judged contribution")}</span>
                    % endif
                % endif
            </td>
            <td style="padding-right:5px;padding-left:5px;">
            <% date = review_manager.getLastReview().getAdjustedEditorDueDate() %>
            % if date is None:
                ${ _("Deadline not set.")}
            % else:
                <span>${ date.strftime(dueDateFormat) }</span>
            % endif
            </td>
        </tr>
    % endfor

</table>
<br>
% endif
% if not ConfReview.getEditedContributions(User):
<p style="padding-left: 25px;"><font color="gray">${ _("No contributions have so far been assigned to you for judgement.")}</font></p>
% endif
