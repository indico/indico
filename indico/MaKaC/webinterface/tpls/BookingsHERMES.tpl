
<form action=<%= postURL %> method="POST">
    <table width="65%" cellspacing="0" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
        <tr>
            <td colspan="3" class="groupTitle"> <%= _("Creating a Meeting on HeRMeS system")%></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"><font color="red">*</font>  <%= _("Meeting Name")%></span></td>
            <td bgcolor="white" width="100%">&nbsp;
                <input type="text" name="title" size="40" value="<%= title %>">
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">  <%= _("Description")%></span></td>
            <td bgcolor="white" width="100%">&nbsp;
                <textarea name="description" cols="43" rows="6"><%= description %></textarea>
            </td>
        </tr>

        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("PIN Code")%></span></td>
            <td bgcolor="white" width="100%">&nbsp;
            <input type="password" size="8" name="PinCode" value="<%= PinCode %>"></td></tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("PIN Code (confirmation)")%></span></td>
            <td bgcolor="white" width="100%">&nbsp;
            <input type="password" size="8" name="ConfirmPinCode" value="<%= ConfirmPinCode %>"></td></tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat">Start date</span></td>
            <td bgcolor="white" width="100%">&nbsp;
                <input type="text" size="2" name="sDay" value="<%= sDay %>">-
                <input type="text" size="2" name="sMonth" value="<%= sMonth %>">-
                <input type="text" size="4" name="sYear" value="<%= sYear %>">
                <a href="" onClick="javascript:window.open('<%= calendarSelectURL %>?daystring=sDay&monthstring=sMonth&yearstring=sYear','calendar','scrollbars=no,menubar=no,width=200,height=170');return false;">
                <img src=<%= calendarIconURL %> alt="open calendar" border="0">
                </a>
                &nbsp;at&nbsp;
                <select name="sHour" value="<%= sHour %>">:
                            <option value="08" selected>08</option>
                            <option value="09">09</option>
                            <option value="10">10</option>
                            <option value="11">11</option>
                            <option value="12">12</option>
                            <option value="13">13</option>
                            <option value="14">14</option>
                            <option value="15">15</option>
                            <option value="16">16</option>
                            <option value="17">17</option>
                            <option value="18">18</option>
                            <option value="19">19</option>
                            <option value="20">20</option>
                            <option value="21">21</option>
                            <option value="22">22</option>
                            <option value="23">23</option></select>
                <select name="sMinute" value="<%= sMinute %>">
                            <option value="00" selected>00</option>
                            <option value="30" >30</option>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("End date")%></span></td>
            <td bgcolor="white" width="100%">&nbsp;
                <input type="text" size="2" name="eDay" value="<%= eDay %>">-
                <input type="text" size="2" name="eMonth" value="<%= eMonth %>">-
                <input type="text" size="4" name="eYear" value="<%= eYear %>">
                <a href="" onClick="javascript:window.open('<%= calendarSelectURL %>?daystring=eDay&monthstring=eMonth&yearstring=eYear','calendar','scrollbars=no,menubar=no,width=200,height=170');return false;">
                <img src=<%= calendarIconURL %> alt="open calendar" border="0">
                </a>
                &nbsp;at&nbsp;
                <select name="eHour" value="<%= eHour %>">:
                            <option value="08">08</option>
                            <option value="09">09</option>
                            <option value="10">10</option>
                            <option value="11">11</option>
                            <option value="12">12</option>
                            <option value="13">13</option>
                            <option value="14">14</option>
                            <option value="15">15</option>
                            <option value="16">16</option>
                            <option value="17">17</option>
                            <option value="18">18</option>
                            <option value="19">19</option>
                            <option value="20" selected>20</option>
                            <option value="21">21</option>
                            <option value="22">22</option>
                            <option value="23">23</option></select>
                <select name="eMinute" value="<%= eMinute %>">
                            <option value="28">28</option>
                            <option value="58" selected>58</option>
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"><font color="red">*</font>  <%= _("Email address or mailing list")%></span></td>
            <td bgcolor="white" width="100%">&nbsp;
            <input type="text" name="UserEmail" size="25" value=""></td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("List of Participants")%></span></td>
            <td bgcolor="white" width="100%" align="left">&nbsp;
                <input type="submit" class="btn" name="addParticipant" value="<%= _("add participant")%>">
                <input type="submit" class="btn" name="RemoveParticipant" value="<%= _("remove participant")%>">
            </td>
        </tr>
        <tr>
            <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Comments or remarks")%></span></td>
            <td bgcolor="white" width="100%">&nbsp;
                <textarea name="comments" cols="43" rows="3"><%= comments %></textarea>
            </td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr align="center">
            <td colspan="2" valign="bottom" align="center">
                <table align="center">
        <tr>
        <td><input type="submit" class="btn" value="<%= _("Create Meeting")%>"></td>
        <td><input type= "submit" name="cancel" value= " <%= _("cancel")%>"></td>
        </tr>
        <tr><td>&nbsp;</td></tr>
        <tr></tr>
        <tr><td></td><td align="left"><small> <%= _("Please note that the fields marked with * are compulsory and all the times are in  GMT+1 timezone.")%></small></td></tr>
                </table>
        </tr>
</table>
</form>