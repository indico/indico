<% from MaKaC.reviewing import ConferenceReview %>
        <table cellspacing="0" cellpadding="0" width="100%%">
            <tr>
                <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
                    <span class="titleCellFormat"><%= _("Judgement")%></span>
                </td>
                <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
                    <span class="titleCellFormat"><%= _("Comments")%></span>
                </td>
                <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
                    <span class="titleCellFormat"><%= _("Approved questions")%></span>
                </td>
                <% if ShowReferee: %>
                <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
                    <span class="titleCellFormat"><%= _("Referee")%></span>
                </td>
                <% end %>
                <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
                    <span class="titleCellFormat"><%= _("Submission date")%></span>
                </td>
            </tr>
            <tr>                    
                <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                    <%= Review.getRefereeJudgement().getJudgement() %>
                </td>
                <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                    <%= Review.getRefereeJudgement().getComments() %>
                </td>
                <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                    <% for q,a in Review.getRefereeJudgement().getAnswers(): %>
                        <%= q %> : <%= ConferenceReview.reviewingQuestionsAnswers[int(a)] %>
                        <br/>
                    <% end %>                
                </td>
                <% if ShowReferee: %>
                <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                    <%= Review.getRefereeJudgement().getAuthor().getFullName() %>
                </td>
                <% end %>
                <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                    <%= Review.getRefereeJudgement().getAdjustedSubmissionDate().strftime(format) %>
                </td>
            </tr>
        </table>