<% declareTemplate(newTemplateStyle=True) %>
<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.conference import LocalFile %>
<% from MaKaC.conference import Link %>

<% for review in Versioning: %>

    <% if review.getRefereeJudgement().isSubmitted(): %>
        <table width="90%%" align="center" border="0">
            <tr>
                <td align="left" colspan="2">
                    <span style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <%= _("Review")%> <%= review.getVersion() %>
                    </span>
                </td>
            </tr>
            <% for m in review.getMaterials(): %>
            <tr>
                <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;">
                    <span style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <%= m.getTitle() %>
                    </span>
                </td>
                <% for res in m.getResourceList(): %>
                <td align="left">
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
                <td width="100%%"></td>
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