<% declareTemplate(newTemplateStyle=True) %>
<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.conference import LocalFile %>
<% from MaKaC.conference import Link %>

<% for review in Versioning: %>

    <% if review.getRefereeJudgement().isSubmitted(): %>
        <table width="90%%" align="center" border="0" style="padding-bottom: 10px;">
		    <tr>
		        <td colspan="3" class="groupTitle" style="padding-top:20px;"><%= _("Judgement details")%></td>
		    </tr>
		    <tr>
		    <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #BBBBBB; padding-top: 5px; padding-bottom: 5px;">
                    <span class="titleCellFormat"><%= _("Judgement version")%></span>
            </td>
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #BBBBBB; padding-top: 5px; padding-bottom: 5px;">
                    <span class="titleCellFormat"><%= _("Type")%></span>
            </td>
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #BBBBBB; padding-top: 5px; padding-bottom: 5px;">
                    <span class="titleCellFormat"><%= _("Material")%></span>
            </td>
            </tr>
            <tr>
            <% for m in review.getMaterials(): %>
                <td>
                    <span style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <%= _("Review")%>: <%= review.getVersion() %>
                    </span>
                </td>
                <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;">
                    <span style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <%= m.getTitle() %>
                    </span>
                </td>   
                <% for res in m.getResourceList(): %>
                <td>
                    <span style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                    <% if isinstance(res, LocalFile): %>
                        <a href="<%= urlHandlers.UHFileAccess.getURL(res) %>">
                    <% end %>
                    <% elif isinstance(res, Link) :%>
                        <a href="<%= res.getURL() %>">
                    <% end %>
                        <%= res.getName() %>
                    </a>
                    </span>
                </td>
                <% end %>
            </tr>
            <% end %>
        </table>
        <% includeTpl ('ContributionReviewingDisplay',
                        Editing = review.getEditorJudgement(), AdviceList = review.getReviewerJudgements(), Review = review,
                        ConferenceChoice = ConferenceChoice) %>
        <br><br><br>
    <% end %>
<% end %>