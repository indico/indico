<%
# Parameters for the cancel button, this since if the
# form is used in an exclusive popup we can pass
# a onclick action that closes the dialog.
if cancelButtonParams is not UNDEFINED:
    cancelButtonParams_ = cancelButtonParams
else:
    cancelButtonParams_ = """ type="submit" """
%>

<DIV ALIGN=CENTER>${ msg }</DIV>
<form action="${ formAction }" method="POST">
     <table class="groupTable">
        % if formTitle:
             <tr>
                 <td colspan="2"><div class="groupTitle">${ formTitle }</div></td>
             </tr>
         % endif
         <tr>
             <td nowrap class="titleCellTD">
                 <span class="titleCellFormat">${ _("Title")}</span>
             </td>
             <td bgcolor="white" width="100%" valign="top" class="blacktext">                 ${ titles }             </td>
         </tr>
         <tr>
             <td nowrap class="titleCellTD">                 <span class="titleCellFormat">${ _("Family name")}</span>             </td>
             <td bgcolor="white" width="100%" valign="top" class="blacktext">                 ${ surName }             </td>
         </tr>
         <tr>
             <td nowrap class="titleCellTD">                 <span class="titleCellFormat">${ _("First name")}</span>             </td>
             <td bgcolor="white" width="100%" valign="top" class="blacktext">                 ${ name }             </td>
         </tr>
         <tr>
             <td nowrap class="titleCellTD">                 <span class="titleCellFormat">${ _("Affiliation")}</span>             </td>
             <td bgcolor="white" width="100%" valign="top" class="blacktext">                 ${ affiliation }             </td>
         </tr>
         <tr>
             <td nowrap class="titleCellTD">                 <span class="titleCellFormat">${ _("Email")}</span>             </td>
             <td bgcolor="white" width="100%" valign="top" class="blacktext">                 ${ email }             </td>
         </tr>
         <tr>
             <td nowrap class="titleCellTD">                 <span class="titleCellFormat">${ _("Address")}</span>             </td>
             <td bgcolor="white" width="100%" valign="top" class="blacktext">                 ${ address }             </td>
         </tr>
         <tr>
             <td nowrap class="titleCellTD">                 <span class="titleCellFormat">${ _("Telephone")}</span>             </td>
             <td bgcolor="white" width="100%" valign="top" class="blacktext">                 ${ phone }             </td>
         </tr>
         <tr>
             <td nowrap class="titleCellTD">                 <span class="titleCellFormat">${ _("Fax")}</span>             </td>
             <td bgcolor="white" width="100%" valign="top" class="blacktext">                 ${ fax }             </td>
         </tr>
         ${ role }
         ${ notice }
         <tr>
             <td></td>
             <td>
                 <input type="submit" class="btn" name="ok" value="${ _("submit")}">
                 <input ${ cancelButtonParams_ } class="btn" name="cancel" value="${ _("cancel")}">
             </td>
         </tr>
     </table>
</form>