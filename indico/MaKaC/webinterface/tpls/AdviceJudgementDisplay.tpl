<% from MaKaC.reviewing import ConferencePaperReview %>
                <tr>
                    <td class="dataCaptionTD" style="width: 25%;padding-right: 1px">
                        <span class="titleCellFormat" style="font-size: 12px;"><%= _("Content judgement:")%></span>
                    </td>
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <%= advice.getJudgement() %>,
                        <em><%= _(" submitted on ") %><%= advice.getAdjustedSubmissionDate().strftime(format) %></em>
                    </td>
                </tr>
                <% if advice.getComments(): %>
                <tr>
                    <td class="dataCaptionTD" style="width: 25%;padding-right: 1px">
                        <span class="titleCellFormat" style="font-size: 12px;"><%= _("Comments:")%></span>
                    </td>
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <%= advice.getComments() %>
                    </td>
                </tr>
                <% end %>
                <% if advice.getAnswers(): %>
                <tr>
                    <td class="dataCaptionTD" style="width: 25%;padding-right: 1px">
                        <span class="titleCellFormat" style="font-size: 12px;"><%= _("Answered questions:")%></span>
                    </td>
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <% for q,a in advice.getAnswers(): %>
                            <%= q %> : <%= ConferencePaperReview.reviewingQuestionsAnswers[int(a)] %>
                            <br/>
                        <% end %>
                    </td>
                </tr>
                <% end %>
                <% if ShowReviewer: %>
                <tr>
                    <td class="dataCaptionTD" style="width: 25%;padding-right: 1px">
                        <span class="titleCellFormat" style="font-size: 12px;"><%= _("Content Reviewer:")%></span>
                    </td>
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <%= advice.getAuthor().getFullName() %>
                    </td>
                </tr>
                <% end %>

