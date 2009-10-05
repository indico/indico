<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% import MaKaC.common.Configuration as Configuration %>

    <% if ConfReview.hasTemplates(): %>
    	<tr>
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
            	<%= _("Name")%>
    	    </td>
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
            	<%= _("Format")%>
    		</td>
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
            	<%= _("Description")%>
    		</td>
        </tr>
    	
    	<% keys = ConfReview.getTemplates().keys() %>
    	<% keys.sort() %>
    	<% for k in keys: %>
    	    <% t = ConfReview.getTemplates()[k] %>
    	<tr>
    		<td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
    		    <a style="color:#5FA5D4" href="<%= urlHandlers.UHDownloadContributionTemplate.getURL(t) %>">
    			    <%= t.getName() %>
    			</a>
                
                <% if CanDelete: %>
                &nbsp;&nbsp;&nbsp;
                <a href="<%= urlHandlers.UHDeleteContributionTemplate.getURL(t) %>">
                    <img class="imglink" style="vertical-align: bottom; width: 15px; height: 15px;" src="<%= Configuration.Config.getInstance().getSystemIconURL("remove") %>" alt="delete template">
                </a>
                <% end %>
    		</td>
    		<td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <%= t.getFormat() %>
            </td>
    		<td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <%= t.getDescription() %>
            </td>
    	</tr>
    	<% end %>
	<% end %>
    <% else: %>
        <tr><td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
            <%= _("No templates have been uploaded yet.")%>
        </td></tr>
    <% end %>

