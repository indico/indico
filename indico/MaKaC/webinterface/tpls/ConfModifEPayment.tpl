
<br>
<table width="90%%" align="left" border="0">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Current status")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext" colspan="2">
            <form action="%(setStatusURL)s" method="POST">
                <input name="changeTo" type="hidden" value="%(changeTo)s"> 
                <b>%(status)s</b> 
                <small><input type="submit" value="%(changeStatus)s"></small>
            </form>
        </td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("detail of Payment")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext">
           <TEXTAREA ROWS="6" COLS="60" disabled="true" >%(detailPayment)s</TEXTAREA>
        </td>
        <td valign="bottom" rowspan="3">
        <form action="%(dataModificationURL)s" method="POST">
			<input type="submit" value="<%= _("modify")%>" %(disabled)s>
		</form>
		</td>
    </tr>
<%
from MaKaC.common import HelperMaKaCInfo
minfo = HelperMaKaCInfo.getMaKaCInfoInstance()
al = minfo.getAdminList()
if al.isAdmin( self._rh._getUser() ):
%>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"><%= _("Mandatory Conditions")%></span></td>
        <td bgcolor="white" width="100%%" class="blacktext">
           <%= _("This conditions are:")%> <b>%(conditionsEnabled)s</b>
           <br/>
           <TEXTAREA ROWS="6" COLS="60" disabled="true" >%(conditionsPayment)s</TEXTAREA>
           <br/>
        </td>
        <td></td>
    </tr>
<%end%>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat">Conditions</span></td>
        <td bgcolor="white" width="100%%" class="blacktext">
           <TEXTAREA ROWS="6" COLS="60" disabled="true" >%(specificConditionsPayment)s</TEXTAREA>
           <br/>
        </td>
        <td></td>
    </tr>
	<tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
    <tr>
        <td class="dataCaptionTD">
          <span class="dataCaptionFormat"> <%= _("Mod of Payments")%></span>
          <br>
          <br>
          <img src=%(enablePic)s alt="<%= _("Click to disable")%>"> <small> <%= _("Enabled section")%></small>
          <br>
          <img src=%(disablePic)s alt="<%= _("Click to enable")%>"> <small> <%= _("Disabled section")%></small>
        </td>
        <td bgcolor="white" width="100%%" class="blacktext" style="padding-left:20px">
            <form action="" method="POST">
            %(sections)s
        </td>
		</form>
    </tr>
	<tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
</table>
<br>


