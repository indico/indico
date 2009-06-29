<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% import MaKaC.common.Configuration as Configuration %>

    <% if ConfReview.hasTemplates(): %>
    	<tr>
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
            	Name
    	    </td>
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
            	Format
    		</td>
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
            	Description
    		</td>
        </tr>
    	
    	<% keys = ConfReview.getTemplates().keys() %>
    	<% keys.sort() %>
    	<% for k in keys: %>
    	    <% t = ConfReview.getTemplates()[k] %>
    	<tr>
    		<td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
    		    <a href="<%= urlHandlers.UHDownloadContributionTemplate.getURL(t) %>">
    			    <%= t.getName() %>
    			</a>
                
                <% if CanDelete: %>
                &nbsp;&nbsp;&nbsp;
                <a href="<%= urlHandlers.UHDeleteContributionTemplate.getURL(t) %>">
                    <img class="imglink" src="<%= Configuration.Config.getInstance().getSystemIconURL("smallDelete") %>" alt="delete template">
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
            No templates have been uploaded yet.
        </td></tr>
    <% end %>

