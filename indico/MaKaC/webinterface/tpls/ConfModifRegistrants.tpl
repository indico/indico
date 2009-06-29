<script type="text/javascript">
<!--
    function selectAcco()
    {
        document.optionForm.accommShowNoValue.checked=true
        if (!document.optionForm.accomm.length)
        {
            document.optionForm.accomm.checked=true
        }else{
            for (i = 0; i < document.optionForm.accomm.length; i++)
            {
                document.optionForm.accomm[i].checked=true
            }
        }
    }

    function unselectAcco()
    {
        document.optionForm.accommShowNoValue.checked=false
        if (!document.optionForm.accomm.length)
        {
            document.optionForm.accomm.checked=false
        }else{
            for (i = 0; i < document.optionForm.accomm.length; i++)
            {
                document.optionForm.accomm[i].checked=false
            }
        }
    }
    function selectEvent()
    {
        document.optionForm.eventShowNoValue.checked=true
        if (!document.optionForm.event.length)
        {
            document.optionForm.event.checked=true
        }else{
            for (i = 0; i < document.optionForm.event.length; i++)
            {
                document.optionForm.event[i].checked=true
            }
        }
    }

    function unselectEvent()
    {
        document.optionForm.eventShowNoValue.checked=false
        if (!document.optionForm.event.length)
        {
            document.optionForm.event.checked=false
        }else{
            for (i = 0; i < document.optionForm.event.length; i++)
        	{
	            document.optionForm.event[i].checked=false
    	    }
        }
    }
    function selectSession()
    {
        document.optionForm.sessionShowNoValue.checked=true
        if (!document.optionForm.session.length)
        {
            document.optionForm.session.checked=true
        }else{
            for (i = 0; i < document.optionForm.session.length; i++)
            {
                document.optionForm.session[i].checked=true
            }
        }
    }

    function unselectSession()
    {
        document.optionForm.sessionShowNoValue.checked=false
        if (!document.optionForm.session.length)
        {
            document.optionForm.session.checked=false
        }else{
            for (i = 0; i < document.optionForm.session.length; i++)
            {
                document.optionForm.session[i].checked=false
            }
        }
    }
    function selectDisplay()
    {
        for (i = 0; i < document.optionForm.disp.length; i++)
        {
        	document.optionForm.disp[i].checked=true
    	}
    }

    function unselectDisplay()
    {
        for (i = 0; i < document.optionForm.disp.length; i++)
    	{
	        document.optionForm.disp[i].checked=false
    	}
    }
    
    function selectUnSelectAll(checkbox)
    {
        for (i = 0; i < document.registrantsForm.registrants.length; i++)
    	{
	        document.registrantsForm.registrants[i].checked=checkbox.checked
    	}
    }
    
    function selectAll()
    {
        if ( document.registrantsForm.registrants ) { // true if there is at least 1 registrant
            if ( !document.registrantsForm.registrants.length) { // true if there is only 1 registrant
                document.registrantsForm.registrants.checked=true
            } else { // there is more than 1 registrant
                for (i = 0; i < document.registrantsForm.registrants.length; i++) {
                    document.registrantsForm.registrants[i].checked=true
                }
            }
        }
    }

    function deselectAll()
    {
        if ( document.registrantsForm.registrants ) { // true if there is at least 1 registrant
            if ( !document.registrantsForm.registrants.length) { // true if there is only 1 registrant
                document.registrantsForm.registrants.checked=false
            } else { // there is more than 1 registrant
                for (i = 0; i < document.registrantsForm.registrants.length; i++) {
                    document.registrantsForm.registrants[i].checked=false
                }
            }
        }
    }
//-->
</script> 




<a href="" name="results"></a>
<table width="100%%" cellspacing="0" align="center" border="0">
	<tr>
	  <td colspan="20" align="left" width="100%%">
		<form action=%(filterPostURL)s method="post" name="optionForm">
		   %(menu)s
		   %(sortingOptions)s
		</form>
	  </td>
	</tr>
    <tr><td>&nbsp;</td></tr>
    <tr>
        <td colspan="20" class="groupTitle">
            <%= _("Current registrants")%> (%(numRegistrants)s)
        </td>
    </tr>
    <tr>
      <td colspan="20" align="left">
    <form action=%(actionPostURL)s method="post" name="registrantsForm">    
    %(printIconURL)s
    %(excelIconURL)s
    %(emailIconURL)s
    %(infoIconURL)s
    <input type="hidden" name="reglist" value="%(reglist)s">
    %(displayOptions)s
      </td>
    </tr>
    <tr>
        <td colspan="20" style="border-bottom:2px solid #777777;padding-top:5px" valign="bottom" align="left">
		    <table>
		        <tbody>
					<td valign="bottom" align="left">
						<input type="submit" class="btn" name="newRegistrant" value="<%= _("Add New")%>">
			        </td>
					<td valign="bottom" align="left">
						<input type="submit" class="btn" name="removeRegistrants" value="<%= _("Remove Selected")%>">
			        </td>
					<td valign="bottom" align="left">
						<input type="submit" class="btn" name="emailSelected" value="<%= _("Email Selected")%>">
			        </td>
					<td valign="bottom" align="left">
						<input type="submit" class="btn" name="printBadgesSelected" value="<%= _("Print Badges for Selected")%>">
			        </td>
			    </tbody>
	        </table>
        </td>
    </tr>
    %(columns)s
    %(registrants)s
	<tr><td>&nbsp;</td></tr>
	<tr>
        <td colspan="20" style="border-top:2px solid #777777;padding-top:5px" valign="bottom" align="left">
		    <table>
		        <tbody>
					<td valign="bottom" align="left">
						<input type="submit" class="btn" name="newRegistrant" value="<%= _("Add New")%>">
			        </td>
					<td valign="bottom" align="left">
						<input type="submit" class="btn" name="removeRegistrants" value="<%= _("Remove Selected")%>">
			        </td>
					<td valign="bottom" align="left">
						<input type="submit" class="btn" name="emailSelected" value="<%= _("Email Selected")%>">
			        </td>
					<td valign="bottom" align="left">
						<input type="submit" class="btn" name="printBadgesSelected" value="<%= _("Print Badges for Selected")%>">
			        </td>
			    </tbody>
	        </table>
        </td>
    </tr>
</table>
</form>
