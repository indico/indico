
<table width="80%%" align="center" border="0" style="border-left: 1px solid #777777">
	<tr>
	  <td class="groupTitle" colspan="2"> <%= _("Task List Management")%></td>
	</tr>
    <tr>
      <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Tasks")%></span></td>
      <td bgcolor="white" width="100%%" class="blacktext">%(tasksAllowed)s</td>
    </tr>
    <tr><td>&nbsp;</td></tr>
	<tr>
  		<td class="groupTitle" colspan="2"> <%= _("Access Control")%></td>  		
	</tr>	
	<form action="%(taskAction)s" method="POST">
	<tr>
	  <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Current status")%></span></td>
	  <td bgcolor="white" width="100%%" valign="top" class="blacktext">
	    %(locator)s
    	<b>%(accessVisibility)s</b> 
	    <small>%(changeAccessVisibility)s</small>
	  </td>
	</tr>
	<tr>
	  <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Users allowed to access")%></span></td>
	  <td bgcolor="white" width="100%%" valign="top" class="blacktext">
	  	<table width="100%%">
	  		<tr>
	  			<td align="right">
	  				<select name="accessChosen">%(accessOptions)s</select>
	  				<input type="submit" name="taskAccessAction" value="<%= _("Add")%>">
	  				<input type="submit" name="taskAccessAction" value="<%= _("New")%>">
	  				<input type="submit" name="taskAccessAction" value="<%= _("Remove")%>">
	  			</td>
	  		</tr>
		  	<tr>
	  			<td>
	  			%(accessList)s
	  			</td>
	  		</tr>		  	
	  	</table>
	  </td>
	</tr>	
	<tr><td>&nbsp;</td></tr>
	<tr>
  		<td class="groupTitle" colspan="2"> <%= _("Comment Rights")%></td>  		
	</tr>	
	<tr>
	  <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Current status")%></span></td>
	  <td bgcolor="white" width="100%%" valign="top" class="blacktext">
	    %(locator)s
    	<b>%(commentVisibility)s</b> 
	    <small>%(changeCommentVisibility)s</small>
	  </td>
	</tr>
	<tr>
	  <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Users allowed to comment")%></span></td>
	  <td bgcolor="white" width="100%%" valign="top" class="blacktext">
	  	<table width="100%%">
	  		<tr>
	  			<td align="right">
	  				<select name="commentChosen">%(commentOptions)s</select>
	  				<input type="submit" name="taskCommentAction" value="<%= _("Add")%>">
	  				<input type="submit" name="taskCommentAction" value="<%= _("New")%>">
	  				<input type="submit" name="taskCommentAction" value="<%= _("Remove")%>">
	  			</td>
	  		</tr>
		  	<tr>
	  			<td>
	  			%(commentList)s
	  			</td>
	  		</tr>		  	
	  	</table>
	  </td>
	</tr>
	
	<tr><td>&nbsp;</td></tr>
	
	<tr>
  		<td class="groupTitle" colspan="2"> <%= _("Modification Control")%></td>
	</tr>
	<tr>
	  <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Task Managers")%></span></td>
	  <td bgcolor="white" width="100%%" valign="top" class="blacktext">
	  	<table width="100%%">
	  		<tr>
	  			<td align="right">
	  				<select name="managerChosen">%(managerOptions)s</select>
	  				<input type="submit" name="taskManagerAction" value="<%= _("Add")%>">
	  				<input type="submit" name="taskManagerAction" value="<%= _("New")%>">
	  				<input type="submit" name="taskManagerAction" value="<%= _("Remove")%>">
	  			</td>
	  		</tr>
		  	<tr>
	  			<td>
	  			%(managerList)s
	  			</td>
	  		</tr>		  	
	  	</table>
	  </td>
	</tr>
	</form>
	<tr><td>&nbsp;</td></tr>
</table>
