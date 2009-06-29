        <div style="overflow: auto;">
		<form action="%(postURL)s" method="POST">
    	<table>
   		    <tr>
		        <td colspan="3" class="groupTitle">%(WPtitle)s</td>
    		</tr>
    		<tr>              
			    <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Family name")%></span></td>
				<td bgcolor="white" width="100%%">
        		    <input type="text" name="surname" size="60" value="%(surName)s">
	        	</td>
		    </tr>
    		<tr>
		        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("First name")%></span></td>
        		<td bgcolor="white" width="100%%">
		            <input type="text" name="firstname" size="60" value="%(firstName)s">
        		</td>
		    </tr>
		    <tr>
        		<td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Email")%></span></td>
        		<td bgcolor="white" width="100%%">
		            <input type="text" name="email" size="60" value="%(email)s">
        		</td>
		    </tr>
		    <tr>
        		<td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Organisation")%></span></td>
		        <td bgcolor="white" width="100%%">
        		    <input type="text" name="organisation" size="60" value="%(organisation)s">
		        </td>
		    </tr>
		</table>
		<div style="width: 400px;">
			<div style="float: left;">%(searchOptions)s</div>
	        <div style="float: right; padding-top: 20px;">
				<input type="submit" class="btn" value="<%= _("search")%>" name="action">
				<input type="button" class="btn" onclick="javascript: $E('addForm').dom.submit();" value="cancel" />
			</div>
        </div>
        </form>
        </div>

		
		<div>
		    %(msg)s
		    <form id="addForm" action="%(addURL)s" method="POST">
		            %(params)s
		            %(searchResultsTable)s
		            %(selectionBox)s    
		    </form>
		</div>
