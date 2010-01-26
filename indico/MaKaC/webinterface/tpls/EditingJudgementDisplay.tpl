<% from MaKaC.reviewing import ConferenceReview %>
            <table cellspacing="0" cellpadding="2" width="100%%" style="padding-bottom: 10px;">
                <tr>
                    <td class="dataCaptionTD" style="width: 25%;padding-right: 1px">
                        <span class="titleCellFormat" style="font-size: 12px;"><strong><%= _("Layout Judgement:")%></strong></span>
                    </td>
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <strong><%= Editing.getJudgement() %></strong>
                    </td>
                </tr>
                <tr>
                    <td class="dataCaptionTD" style="width: 25%;padding-right: 1px">
                        <span class="titleCellFormat" style="font-size: 12px;"><%= _("Comments:")%></span>
                    </td>
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <%= Editing.getComments() %>
                    </td>
                </tr>
                <tr>
                    <td class="dataCaptionTD" width="100%" style="width: 25%;padding-right: 1px">
                        <span class="titleCellFormat" style="font-size: 12px;"><%= _("Criteria Evaluation:")%></span>
                    </td>
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <% for q,a in Editing.getAnswers(): %>
                            <%= q %> : <%= ConferenceReview.reviewingQuestionsAnswers[int(a)] %>
                            <br/>
                        <% end %>
                    </td>
                </tr>
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
                <tr>
                    <td class="dataCaptionTD" style="width: 25%;padding-right: 1px">
                        <span class="titleCellFormat" style="font-size: 12px;"><%= _("Submission date:")%></span>
                    </td>
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <%= Editing.getAdjustedSubmissionDate().strftime(format) %>
                    </td>
                </tr>
            </table>