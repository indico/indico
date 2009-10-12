<% from MaKaC.reviewing import ConferenceReview %>
            <table cellspacing="0" cellpadding="5" width="100%%">
                <tr>
                    <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #BBBBBB;">
                        <span class="titleCellFormat"><%= _("Judgement")%></span>
                    </td>
                    <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #BBBBBB;">
                        <span class="titleCellFormat"><%= _("Comments")%></span>
                    </td>
                    <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #BBBBBB;">
                        <span class="titleCellFormat"><%= _("Criteria Evaluation")%></span>
                    </td>
                    <% if ShowEditor: %>
                    <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #BBBBBB;">
                        <span class="titleCellFormat"><%= _("Layout Reviewer")%></span>
                    </td>
                    <% end %>
                    <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #BBBBBB;">
                        <span class="titleCellFormat"><%= _("Submission date")%></span>
                    </td>
                </tr>
                <tr>                    
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <%= Editing.getJudgement() %>
                    </td>
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <%= Editing.getComments() %>
                    </td>
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <% for q,a in Editing.getAnswers(): %>
                            <%= q %> : <%= ConferenceReview.reviewingQuestionsAnswers[int(a)] %>
                            <br/>
                        <% end %>
                    </td>
                    <% if ShowEditor: %>
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <%= Editing.getAuthor().getFullName() %>
                    </td>
                    <% end %>
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <%= Editing.getAdjustedSubmissionDate().strftime(format) %>
                    </td>
                </tr>
            </table>