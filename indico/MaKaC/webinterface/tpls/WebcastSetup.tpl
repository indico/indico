<table align="center" width="95%">
<tr>
  <td>
    <br />
    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
      <td class="groupTitle">Channels</td>
    </tr>
    <tr>
      <td>
  <%= channels %>
  <form action="<%= postURL %>" method="POST">
  <table bgcolor="#bbbbbb">
  <tr bgcolor="#999999"><td colspan=2><font color=white>New Channel</font>
  </td></tr><tr><td>
  name:</td><td><input name="chname" size=30>
  </td></tr><tr><td>
  url:</td><td><input name="churl" size=30>
  </td></tr><tr><td>
  width:</td><td><input name="chwidth" size=4>
  </td></tr><tr><td>
  height:</td><td><input name="chheight" size=4>
  </td></tr><tr><td colspan=2>
  <input type="submit" name="submit" value="add channel">
  </td></tr>
  </table>
  </form>
      </td>
    </tr>
    </table>

    <br /><br />

    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
      <td class="groupTitle">Webcast Synchronization</td>
    </tr>
    <tr>
      <td bgcolor="white" width="100%" valign="top" class="blacktext" style="padding-top: 10px;">
        <form action="<%= saveWebcastSynchronizationURL %>" method="POST">
          <span>Synchronization URL: </span>
          <input name="webcastSynchronizationURL" size="50" value="<%= webcastSynchronizationURL %>"/>
          <input type="submit" name="submit" value="Save">
        </form>
        <div style="padding-top: 10px;padding-bottom: 10px;">
          Used to automatically synchronize every time:
          <ul style="padding:0;margin:0;margin-left: 50px;">
              <li>
                  Something in the "Live channels" section is changed.
              </li>
              <li>
                  An event is added or removed from "Forthcoming webcasts"
              </li>
          </ul>
          Leave empty for no automatic synchronization.
        </div>
        <form action="<%= webcastManualSynchronize %>" method="POST">
            <input type="submit" name="submit" value="Synchronize manually">
            <span>Remember to save the URL first if you have modified it.</span>
        </form>
      </td>
    </tr>
    </table>

    <br /><br />

    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
      <td class="groupTitle">Webcast Administrators list</td>
    </tr>
    <tr>
      <td bgcolor="white" width="100%" valign="top" class="blacktext">
	<%= adminList %>
      </td>
    </tr>
    </table>
  </td>
</tr>
</table>
<br /><br />
