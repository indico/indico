<br>
<table width="100%" cellpadding="0" cellspacing="0" border="0">
  <tr>
    <td valign="bottom">
    	<span class="categorytitle"><%= name %></span>
    	<span class="categoryManagers"><%= managers %></span>
    </td>
  </tr>
  <tr>
    <td class="subtitle" width="100%">
      <%= description %>
    </td>
    <td class="subtitle">
    	<a href="<%= conferenceList %>"> <%= _("Conference&nbsp;List&nbsp;")%></a>
    </td>
  </tr>

  <tr><td>&nbsp;</td></tr>
  <tr>
    <td class="menutitle" colspan="2">
      <%= taskCommentTitle %>
    </td>
  </tr>
  <tr><td colspan="2">&nbsp;</td></tr>
  <tr>
    <td colspan="2" align="right">
      <a href="<%= taskList %>"> <%= _("Task&nbsp;List&nbsp;")%></a>
    </td>
  </tr>
  <tr>
    <td colspan="2" align="center">
		<form method="post" action="<%= taskCommentAction %>">
    	<table width="70%">
		    <tr>
    			<td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Task Id")%></span></td>
    			<td>
    				&nbsp;<%= taskId %>
    				<input type="hidden" name="taskId" value="<%= taskId %>">
    			</td>
    		</tr>
    		<tr>
    			<td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Created by")%></span></td>
    			<td>
    				&nbsp;<%= createdBy %>
    				<input type="hidden" name="createdBy" value="<%= creatorId %>">
    			</td>
    		</tr>
    		<tr>
    			<td nowrap class="titleCellTD"><span class="titleCellFormat">
		    		 <%= _("Title")%>
    			</span></td>
    			<td>&nbsp;<%= taskTitle %></td>
    		</tr>
    		<tr>
    			<td nowrap class="titleCellTD"><span class="titleCellFormat">
		    		 <%= _("Status")%>
    			</span></td>
    			<td>&nbsp;<%= taskStatus %></td>
    		</tr>
    		<tr>
    			<td nowrap class="titleCellTD"><span class="titleCellFormat">
		    		 <%= _("Description")%>
    			</span></td>
    			<td>&nbsp;<%= taskDescription %></td>
    		</tr>
    		<tr>
    			<td nowrap class="titleCellTD"><span class="titleCellFormat">
		    		 <%= _("Responsible")%>
    			</span></td>
    			<td>&nbsp;<%= responsibleList %></td>
    		</tr>
    		<tr>
    			<td nowrap class="titleCellTD"><span class="titleCellFormat">
		    		 <%= _("Commented by")%>
    			</span></td>
    			<td>&nbsp;<%= commentedBy %></td>
    		</tr>
    		<tr>
    			<td nowrap class="titleCellTD"><span class="titleCellFormat">
		    		 <%= _("Comment text")%>
    			</span></td>
    			<td><%= commentText %></td>
    		</tr>
    		<tr><td>&nbsp;</td></tr>
    		<tr align="center">
    	        <td colspan="2" style="border-top:1px solid #777777;" valign="bottom" align="center">
        	        <table align="center">
            	        <tr>
                	        <td><input type="submit" class="btn" value="<%= _("ok")%>" name="performedAction"></td>
                    	    <td><input type="submit" class="btn" value="<%= _("cancel")%>" name="cancel"></td>
	                    </tr>
    	            </table>
        	    </td>
        	</tr>
    	</table>
    	</form>
    </td>
  </tr>
</table>
