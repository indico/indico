<% from MaKaC.reviewing import ConferencePaperReview %>
            <table cellspacing="0" cellpadding="2" width="100%%" >
                <tr>
                    <td class="dataCaptionTD" style="width: 25%;padding-right: 1px">
                        <span class="titleCellFormat" style="font-size: 12px;"><%= _("Layout judgement:")%></span>
                    </td>
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <%= Editing.getJudgement() %>,
                        <em><%= _(" submitted on ") %><%= Editing.getAdjustedSubmissionDate().strftime(format) %></em>
                    </td>
                </tr>
                <% if Editing.getComments(): %>
                <tr>
                    <td class="dataCaptionTD" style="width: 25%;padding-right: 1px">
                        <span class="titleCellFormat" style="font-size: 12px;"><%= _("Comments:")%></span>
                    </td>
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <%= Editing.getComments() %>
                    </td>
                </tr>
                <% end %>
                <% if Editing.getAnswers(): %>
                <tr>
                    <td class="dataCaptionTD" width="100%" style="width: 25%;padding-right: 1px">
                        <span class="titleCellFormat" style="font-size: 12px;"><%= _("Criteria Evaluation:")%></span>
                    </td>
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <% for q,a in Editing.getAnswers(): %>
                            <%= q %> : <%= ConferencePaperReview.reviewingQuestionsAnswers[int(a)] %>
                            <br/>
                        <% end %>
                    </td>
                </tr>
                <% end %>
                <% if ShowEditor: %>
                <tr>
                    <td class="dataCaptionTD" style="width: 25%;padding-right: 1px">
                        <span class="titleCellFormat" style="font-size: 12px;"><%= _("Layout Reviewer:")%></span>
                    </td>
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <%= Editing.getAuthor().getFullName() %>
                    </td>
                </tr>
                <% end %>
            </table>