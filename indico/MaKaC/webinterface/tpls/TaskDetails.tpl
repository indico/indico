<br>
<table width="100%%" cellpadding="0" cellspacing="0" border="0">
  <tr>
    <td valign="bottom">
    	<span class="categorytitle">%(name)s</span>
    	<span class="categoryManagers">%(managers)s</span>
    </td>
  </tr>
  <tr>
    <td class="subtitle" width="100%%">
      %(description)s
    </td>
    <td class="subtitle">
    	<a href="%(conferenceList)s"> <%= _("Conference&nbsp;List&nbsp;")%></a>
    </td>
  </tr>

  <tr><td>&nbsp;</td></tr>
  <tr>
    <td class="menutitle" colspan="2">
      %(taskDetailsTitle)s
    </td>
  </tr>
  <tr><td colspan="2">&nbsp;</td></tr>
  <tr>
    <td colspan="2" align="right">
      <a href="%(taskList)s"> <%= _("Task&nbsp;List&nbsp;")%></a>
    </td>
  </tr>
  <tr>
    <td colspan="2" align="center">
		<form method="post" action="%(taskDetailsAction)s">    	
		<input type="hidden" name="editRights" value="%(editRights)s">
    	<table width="70%%">
		    <tr>
    			<td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Task Id")%></span></td>
    			<td>
    				&nbsp;%(taskId)s
    				<input type="hidden" name="taskId" value="%(taskId)s">
    			</td>
    		</tr>
    		<tr>
    			<td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Created by")%></span></td>
    			<td>
    				&nbsp;%(createdBy)s
    				<input type="hidden" name="createdBy" value="%(creatorId)s">
    			</td>
    		</tr>
    		<tr>
    			<td nowrap class="titleCellTD"><span class="titleCellFormat">
		    		 <%= _("Title")%>
    			</span></td>
    			<td>&nbsp;%(taskTitle)s</td>
    		</tr>
    		<tr>
    			<td nowrap class="titleCellTD"><span class="titleCellFormat">
		    		 <%= _("Status")%>
    			</span></td>
    			<td>
 		   			<table width="100%%">
    					<tr>
    						<td >%(taskStatus)s</td>
    						<td align="right">
    							<select name="changedStatus" %(statusDisabled)s>%(taskStatusOptions)s</select>    							
	    					</td>
	    					<td width="29%%">
		    					&nbsp;<input type="submit" class="btn" name="performedAction" value="<%= _("Change status")%>" %(statusDisabled)s>
	    					</td>
    					</tr>
    				</table>
    			</td>
    		</tr>
    		<tr>
    			<td nowrap class="titleCellTD"><span class="titleCellFormat">
		    		 <%= _("Description")%>
    			</span></td>
    			<td>%(taskDescription)s</td>
    		</tr>
    		%(responsible)s
    		<tr>
    			<td nowrap class="titleCellTD"><span class="titleCellFormat">
		    		 <%= _("Comments")%>
    			</span></td>
    			<td>
    			<table width="100%%">
    				<tr>
	        			<td>
	        				%(showCommentsButton)s
	        				%(showComments)s
	        			</td>
	        			<td width="29%%">&nbsp;%(newCommentButton)s</td>
        			</tr>
        			<tr>
        				<td colspan="2">%(commentsList)s</td>
        			</tr>
        		</table>
    			</td>
    		</tr>
    		<tr>
    			<td nowrap class="titleCellTD"><span class="titleCellFormat">
		    		 <%= _("Status history")%>
    			</span></td>
    			<td>
    			<table width="100%%">
	    			<tr>
    					<td>
    						%(showStatusButton)s
    						%(showStatus)s
    					</td>
    				</tr>
    				<tr>
    					<td>%(statusList)s</td>
    				</tr>
    			</table>
    			</td>
    		</tr>
    		<tr><td>&nbsp;</td></tr>	        
    	</table>
    	</form>
    </td>
  </tr>
</table>

