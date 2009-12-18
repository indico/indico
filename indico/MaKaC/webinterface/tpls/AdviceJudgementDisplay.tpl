<% from MaKaC.reviewing import ConferenceReview %>
                <tr>
                    <td class="dataCaptionTD" style="width: 25%;padding-right: 1px">
                        <span class="titleCellFormat" style="font-size: 12px;"><strong><%= _("Content judgement:")%></strong></span>
                    </td>
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <%= advice.getJudgement() %>
                    </td>
                </tr>
                <tr>
                    <td class="dataCaptionTD" style="width: 25%;padding-right: 1px">
                        <span class="titleCellFormat" style="font-size: 12px;"><%= _("Comments:")%></span>
                    </td>
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <%= advice.getComments() %>
                    </td>
                </tr>
                <tr>
                    <td class="dataCaptionTD" style="width: 25%;padding-right: 1px">
                        <span class="titleCellFormat" style="font-size: 12px;"><%= _("Approved questions:")%></span>
                    </td>
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <% for q,a in advice.getAnswers(): %>
                            <%= q %> : <%= ConferenceReview.reviewingQuestionsAnswers[int(a)] %>
                            <br/>
                        <% end %>
                    </td>
                </tr>
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
                <tr>
                    <td class="dataCaptionTD" style="width: 25%;padding-right: 1px">
                        <span class="titleCellFormat" style="font-size: 12px;"><%= _("Submission date:")%></span>
                    </td>
                    <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <%= advice.getAdjustedSubmissionDate().strftime(format) %>
                    </td>
                
                    
                </tr>
