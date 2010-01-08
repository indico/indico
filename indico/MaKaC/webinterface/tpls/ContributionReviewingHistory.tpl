<% declareTemplate(newTemplateStyle=True) %>
<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.conference import LocalFile %>
<% from MaKaC.conference import Link %>

<% for review in Versioning: %>

    <% if review.getRefereeJudgement().isSubmitted(): %>
        <table width="90%%" align="center" border="0" style="padding-bottom: 10px;">
		    <tr>
<<<<<<< HEAD:indico/MaKaC/webinterface/tpls/ContributionReviewingHistory.tpl
		        <td colspan="3" class="groupTitle" style="width: 60%;padding-top:20px; border-bottom: none">
=======
		        <td colspan="3" class="groupTitle" style="padding-top:20px; border-bottom: none; font-size: 20px;">
>>>>>>> 4608831... [FIXES] - task #108 + small layout fixes:indico/MaKaC/webinterface/tpls/ContributionReviewingHistory.tpl
		          <%= _("Judgement details for ")%><%= _("Review ")%> <%= review.getVersion() %>
		        </td>
		    </tr>
		</table>
            
            <table width="90%%" align="center" border="0" style="padding-bottom: 10px;">
                <tr>
		            <td colspan="1" class="dataCaptionTD" style="width: 25%;padding-right: 1px">
		                    <span class="titleCellFormat" style="font-size: 12px;"><strong><%= _("Material:")%></strong></span>
		            </td>
		            <td>
		             <% for m in review.getMaterials(): %>
		                <% for res in m.getResourceList(): %>
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
		                <br/>
		                <% end %>
		            <% end %>
		            </td>
	            </tr>
	        </table>
           
        <% includeTpl ('ContributionReviewingDisplay',
                        Editing = review.getEditorJudgement(), AdviceList = review.getReviewerJudgements(), Review = review,
                        ConferenceChoice = ConferenceChoice) %>
        
    <% end %>
<% end %>