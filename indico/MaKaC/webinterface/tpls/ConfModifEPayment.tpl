
<br>
<table width="90%" align="left" border="0">
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("Current status")%></span></td>
        <td bgcolor="white" width="100%" class="blacktext" colspan="2">
            <form action="<%= setStatusURL %>" method="POST">
                <input name="changeTo" type="hidden" value="<%= changeTo %>">
                <b><%= status %></b>
                <small><input type="submit" value="<%= changeStatus %>"></small>
            </form>
        </td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> <%= _("detail of Payment")%></span></td>
        <td bgcolor="white" width="100%" class="blacktext">
           <TEXTAREA ROWS="6" COLS="60" disabled="true" ><%= detailPayment %></TEXTAREA>
        </td>
        <td valign="bottom" rowspan="3">
        <form action="<%= dataModificationURL %>" method="POST">
			<input type="submit" value="<%= _("modify")%>" <%= disabled %>>
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
        <td bgcolor="white" width="100%" class="blacktext">
           <%= _("This conditions are:")%> <b><%= conditionsEnabled %></b>
           <br/>
           <TEXTAREA ROWS="6" COLS="60" disabled="true" ><%= conditionsPayment %></TEXTAREA>
           <br/>
        </td>
        <td></td>
    </tr>
<%end%>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat">Conditions</span></td>
        <td bgcolor="white" width="100%" class="blacktext">
           <TEXTAREA ROWS="6" COLS="60" disabled="true" ><%= specificConditionsPayment %></TEXTAREA>
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
          <img src=<%= enablePic %> alt="<%= _("Click to disable")%>"> <small> <%= _("Enabled section")%></small>
          <br>
          <img src=<%= disablePic %> alt="<%= _("Click to enable")%>"> <small> <%= _("Disabled section")%></small>
        </td>
        <td bgcolor="white" width="100%" class="blacktext" style="padding-left:20px">
            <form action="" method="POST">
            <%= sections %>
        </td>
		</form>
    </tr>
	<tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
</table>
<br>

