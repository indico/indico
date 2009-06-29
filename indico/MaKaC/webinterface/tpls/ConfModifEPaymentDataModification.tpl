
<form action=%(postURL)s method="POST">
    <table width="80%%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2"> <%= _("Configuration of pay later")%></td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="titleCellFormat"> <%= _("detail of payment")%></span></td>
            <td align="left"><TEXTAREA name="detailPayment" ROWS="6" COLS="60">%(detailPayment)s</TEXTAREA></td>
        </tr>
<%
from MaKaC.common import HelperMaKaCInfo
minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
al = minfo.getAdminList()
if al.isAdmin( self._rh._getUser() ):
%>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="titleCellFormat"><%= _("Enable conditions")%></span></td>
            <td align="left"><input type="checkbox" name="conditionsEnabled" %(conditionsEnabled)s/> <%= _("Check the box to activate the conditions")%></TEXTAREA></td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="titleCellFormat"><%= _("Mandatory Conditions")%></span></td>
            <td align="left"><TEXTAREA name="conditionsPayment" ROWS="6" COLS="60">%(conditionsPayment)s</TEXTAREA></td>
        </tr>
<%end%>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="titleCellFormat">Conditions</span></td>
            <td align="left"><TEXTAREA name="specificConditionsPayment" ROWS="6" COLS="60">%(specificConditionsPayment)s</TEXTAREA></td>
        </tr>
		<tr><td>&nbsp;</td></tr>
        <tr>
            <td colspan="2" align="left"><input type="submit" value="OK">&nbsp;<input type="submit" value="<%= _("cancel")%>" name="cancel"></td>
        </tr>
    </table>
</form>
