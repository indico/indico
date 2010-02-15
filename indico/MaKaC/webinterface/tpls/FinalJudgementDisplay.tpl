<% from MaKaC.reviewing import ConferenceReview %>
        <table cellspacing="0" cellpadding="2" width="100%%">
            <tr>
                <td class="dataCaptionTD" style="width: 25%;padding-right: 1px">
                    <span class="titleCellFormat" style="font-size: 12px;"><strong><%= _("Final Judgement:")%></strong></span>
                </td>
                <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                    <strong><%= Review.getRefereeJudgement().getJudgement() %></strong>,
                    <%= _(" submitted on ") %><%= Review.getRefereeJudgement().getAdjustedSubmissionDate().strftime(format) %>
                </td>
           </tr>
           <% if Review.getRefereeJudgement().getComments(): %>
           <tr>     
                <td class="dataCaptionTD" style="width: 25%;padding-right: 1px">
                    <span class="titleCellFormat" style="font-size: 12px;"><%= _("Comments:")%></span>
                </td>
                <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                    <%= Review.getRefereeJudgement().getComments() %>
                </td>
           </tr>
           <% end %>
           <% if Review.getRefereeJudgement().getAnswers(): %>
           <tr>
                <td class="dataCaptionTD" style="width: 25%;padding-right: 1px">
                    <span class="titleCellFormat" style="font-size: 12px;"><%= _("Approved questions:")%></span>
                </td>
                <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                    <% for q,a in Review.getRefereeJudgement().getAnswers(): %>
                        <%= q %> : <%= ConferenceReview.reviewingQuestionsAnswers[int(a)] %>
                        <br/>
                    <% end %>                
                </td>
          </tr>
          <% end %>
          <% if ShowReferee: %>
          <tr>
                <td class="dataCaptionTD" style="width: 25%;padding-right: 1px">
                    <span class="titleCellFormat" style="font-size: 12px;"><%= _("Referee:")%></span>
                </td>
                <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                    <%= Review.getRefereeJudgement().getAuthor().getFullName() %>
                </td>
         </tr>
         <% end %>
        </table>