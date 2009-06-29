<% from MaKaC.reviewing import ConferenceReview %>
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
                    <% if ShowReviewer: %>
                    <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
                        <span class="titleCellFormat"><%= _("Reviewer")%></span>
                    </td>
                    <% end %>
                    <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
                        <span class="titleCellFormat"><%= _("Submission date")%></span>
                    </td>
                </tr>
                <tr>                    
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <%= advice.getJudgement() %>
                    </td>
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <%= advice.getComments() %>
                    </td>
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <% for q,a in advice.getAnswers(): %>
                            <%= q %> : <%= ConferenceReview.reviewingQuestionsAnswers[int(a)] %>
                            <br/>
                        <% end %>
                    </td>
                    <% if ShowReviewer: %>
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <%= advice.getAuthor().getFullName() %>
                    </td>
                    <% end %>
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <%= advice.getAdjustedSubmissionDate().strftime(format) %>
                    </td>
                </tr>
