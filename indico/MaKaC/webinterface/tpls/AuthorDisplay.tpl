
<table width="75%" align="center">
	<tr>
        <td colspan="2">
		    <br>
            <table width="100%" align="center" border="0" style="border-left: 1px solid #777777;border-top: 1px solid #777777;">
              <tr>
                <td colspan="3" class="groupTitle" style="background:#E5E5E5; color:gray"> <%= _("Details for")%> <%= title %> <%= fullName %></td>
              </tr>
              <tr>
                <td bgcolor="white">
                  <table width="100%" bgcolor="white" cellpadding="0" cellspacing="0">
                    <tr>
                      <td>
                        <table width="100%">
                          <tr>
                            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Affiliation")%></span></td>
                            <td bgcolor="white" width="100%" valign="top" class="blacktext">&nbsp;&nbsp;&nbsp;<%= organisation %></td>
                          </tr>
                          <tr>
                            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Email")%></span></td>
                            <td bgcolor="white" width="100%" valign="top" class="blacktext"><a href="<%= mailURL %>"><%= email %></a></a></td>
                          </tr>
                          <tr>
                            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Address")%></span></td>
                            <td bgcolor="white" width="100%" valign="top" class="blacktext"><pre>&nbsp;&nbsp;<%= address %></pre></td>
                          </tr>
                          <tr>
                            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Telephone")%></span></td>
                            <td bgcolor="white" width="100%" valign="top" class="blacktext">&nbsp;&nbsp;&nbsp;<%= telephone %></td>
                          </tr>
                          <tr>
                            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Fax")%></span></td>
                            <td bgcolor="white" width="100%" valign="top" class="blacktext">&nbsp;&nbsp;&nbsp;<%= fax %></td>
                          </tr>
                        </table>
                      </td>
                    </tr>
                  </table>
                  <br>
                </td>
              </tr>
      	    </table>
	     </td>
	   </tr>
	   <tr>
          <td colspan="2" >
		    <br>
            <table width="100%" align="center" border="0" style="border-left: 1px solid #777777;border-top: 1px solid #777777;">
              <tr>
                <td colspan="2" class="groupTitle" style="background:#E5E5E5; color:gray"> <%= _("Author in the following contribution(s)")%></td>
              </tr>
              <tr>
                <td>
                  <table width="100%" bgcolor="white" cellpadding="0" cellspacing="0">
                    <tr>
					  <td bgcolor="white" nowrap valign="top" class="blacktext">
                        <%= contributions %>
                      </td>
                    </tr>
                  </table>
                  <br>
                </td>
              </tr>
      	    </table>
      	  </td>
	    </tr>
</table>
