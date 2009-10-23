<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% import MaKaC.common.Configuration as Configuration %>

    <% if ConfReview.hasTemplates(): %>
    <!-- here to put table for the uploaded templates info :) -->
    	<tr>
            <td nowrap width="10%%" class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #DDDDDD;">
            	<%= _("Name")%>
    	    </td>
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #DDDDDD;">
            	<%= _("Format")%>
    		</td>
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #DDDDDD;">
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
    	<tr><td style="padding-bottom:15px;"></td></tr>
        <tr><td colspan="5" style="padding-top: 20px;">
            <em><%= _("To assign team for Paper Review Module, please click on 'Team' and follow the steps")%></em>
        </td></tr>
	<% end %>
    <% else: %>
        <tr><td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
            <%= _("No templates have been uploaded yet.")%>
        </td></tr>
        <tr><td colspan="5" style="padding-top: 20px;">
            <em><%= _("To assign team for Paper Review Module, please click on 'Team' and follow the steps")%></em>
        </td></tr>
    <% end %>

