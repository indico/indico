<%!
# Parameters for the cancel button, this since if the
# form is used in an exclusive popup we can pass 
# a onclick action that closes the dialog.
try:
    cancelButtonParams
except NameError:
    cancelButtonParams = """ type="submit" """
%>

<DIV ALIGN=CENTER>%(msg)s</DIV> 
<form action="%(formAction)s" method="POST">
     <table class="groupTable">
        <% if formTitle: %>
             <tr>
                 <td colspan="2"><div class="groupTitle">%(formTitle)s</div></td>
             </tr>
         <% end %>
         <tr>
             <td nowrap class="titleCellTD">
             	<span class="titleCellFormat"><%= _("Title")%></span>
             </td>             
             <td bgcolor="white" width="100%%" valign="top" class="blacktext"> 				%(titles)s             </td>
         </tr>
         <tr>
             <td nowrap class="titleCellTD">             	<span class="titleCellFormat"><%= _("Family name")%></span>             </td>
             <td bgcolor="white" width="100%%" valign="top" class="blacktext">                 %(surName)s             </td>
         </tr>
         <tr>
             <td nowrap class="titleCellTD">                 <span class="titleCellFormat"><%= _("First name")%></span>             </td>
             <td bgcolor="white" width="100%%" valign="top" class="blacktext"> 				%(name)s             </td>
         </tr>
         <tr>
             <td nowrap class="titleCellTD">                 <span class="titleCellFormat"><%= _("Affiliation")%></span>             </td>
             <td bgcolor="white" width="100%%" valign="top" class="blacktext">                 %(affiliation)s             </td>
         </tr>
         <tr>
             <td nowrap class="titleCellTD">                 <span class="titleCellFormat"><%= _("Email")%></span>             </td>
             <td bgcolor="white" width="100%%" valign="top" class="blacktext">                 %(email)s             </td>
         </tr>
         <tr>
             <td nowrap class="titleCellTD">                 <span class="titleCellFormat"><%= _("Address")%></span>             </td>
             <td bgcolor="white" width="100%%" valign="top" class="blacktext">                 %(address)s             </td>
         </tr>
         <tr>
             <td nowrap class="titleCellTD">                 <span class="titleCellFormat"><%= _("Telephone")%></span>             </td>
             <td bgcolor="white" width="100%%" valign="top" class="blacktext">                 %(phone)s             </td>
         </tr>
         <tr>
             <td nowrap class="titleCellTD">                 <span class="titleCellFormat"><%= _("Fax")%></span>             </td>
             <td bgcolor="white" width="100%%" valign="top" class="blacktext">                 %(fax)s             </td>
         </tr>         
         %(role)s 		
         %(notice)s         
         <tr>
             <td></td>
             <td>
                 <input type="submit" class="btn" name="ok" value="<%= _("submit")%>">
                 <input <%= cancelButtonParams %> class="btn" name="cancel" value="<%= _("cancel")%>">
             </td>
         </tr>
     </table>
</form> 
