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
    	<a href="%(conferenceList)s"><%= _("Conference&nbsp;List")%></a>
    </td>
  </tr>

  <tr><td>&nbsp;</td></tr>
  <tr>
    <td class="menutitle" colspan="2">
       <%= _("Tasks in this category")%>:
    </td>
  </tr>
  <tr>
    <td colspan="2">
    	<table width="100%%">
		    <tr><td>
    		<table width="100%%">
    		<form name="taskManagement" method="post" action="%(taskManagementAction)s">
    			<tr>
	    			<td width="55%%">&nbsp;</td>
	    			<td width="30%%">
	    				<select name="filter">
	    					%(filterOptions)s
	    				</select>
						&nbsp;<input type="submit" class="btn" name="actionPerformed" value="<%= _("Apply filter")%>">
	    			</td>
    				<td width="8%%" align="center">
    					&nbsp;<input type="submit" class="btn" name="actionPerformed" value="<%= _("New task")%>">
					</td>
    			</tr>
    		</form>
    		</table>
    		</td></tr>
    		<tr><td>
    		<table width="100%%">
	    		<tr>
	    			<td width="5%%" class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"><a href="%(idURL)s">&nbsp; <%= _("Id")%></a></td>
	    			<td width="47%%" class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"><a href="%(titleURL)s">&nbsp; <%= _("Title")%></a></td>
		    		<td width="13%%" class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"><a href="%(statusURL)s">&nbsp; <%= _("Status")%></a></td>
		    		<td width="15%%" class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"><a href="%(dateURL)s">&nbsp; <%= _("Creation&nbsp;Date")%></a></td>
	    			<td width="12%%" class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"><a href="">&nbsp; <%= _("No.&nbsp;comments")%></a></td>
	    			<td width="8%%" class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"><a href="">&nbsp;</a></td>
    			</tr>
	    		<tr>
	    			<td>
	    				%(contents)s
    				</td>
    			</tr>
    		</table>
    		</td></tr>
    	</table>
    </td>
  </tr>
</table>

