
<form action=${ postURL } method="POST">
    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle" colspan="2"> ${ _("Configuration of pay later")}</td>
        </tr>
        <tr>
             <td nowrap class="dataCaptionTD"><span class="titleCellFormat">${ _("Currency")}</span></td>
             <td class="blacktext"><select name="Currency">${ Currency }</select></td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="titleCellFormat"> ${ _("Detail of payment")}</span></td>
            <td align="left"><TEXTAREA name="detailPayment" ROWS="6" COLS="60">${ detailPayment }</TEXTAREA></td>
        </tr>
<%
from MaKaC.common import HelperMaKaCInfo
minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
al = minfo.getAdminList()
%>
% if al.isAdmin( self_._rh._getUser() ):
        <tr>
            <td nowrap class="dataCaptionTD"><span class="titleCellFormat">${ _("Enable conditions")}</span></td>
            <td align="left"><input type="checkbox" name="conditionsEnabled" ${ conditionsEnabled }/> ${ _("Check the box to activate the conditions")}</TEXTAREA></td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="titleCellFormat">${ _("Mandatory Conditions")}</span></td>
            <td align="left"><TEXTAREA name="conditionsPayment" ROWS="6" COLS="60">${ conditionsPayment }</TEXTAREA></td>
        </tr>
% endif
        <tr>
            <td nowrap class="dataCaptionTD"><span class="titleCellFormat">Conditions</span></td>
            <td align="left"><TEXTAREA name="specificConditionsPayment" ROWS="6" COLS="60">${ specificConditionsPayment }</TEXTAREA></td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="titleCellFormat">${ _("Payment Summary Email Message")}</span></td>
            <td align="left">
                ${_("Currently this email is")} <strong>${ receiptMsgPaymentEnabled }</strong> (${_("You can change this in the")} <a href="${ dataModificationURL }">${_("registration form setup")}</a>)<br>
                <textarea name="receiptMsgPayment" rows="6" cols="60">${ receiptMsgPayment }</textarea>
            </td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="titleCellFormat">${ _("Success Email Message")}</span></td>
            <td align="left">
                ${_("Currently this email is")} <strong>${ successMsgPaymentEnabled }</strong> (${_("You can change this in the")} <a href="${ dataModificationURL }">${_("registration form setup")}</a>)<br>
                <textarea name="successMsgPayment" rows="6" cols="60">${ successMsgPayment }</textarea>
            </td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr>
            <td colspan="2" align="left"><input type="submit" value="OK">&nbsp;<input type="submit" value="${ _("cancel")}" name="cancel"></td>
        </tr>
    </table>
</form>
