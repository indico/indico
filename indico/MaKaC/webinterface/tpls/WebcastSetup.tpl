<table align="center" width="95%%">
<tr>
  <td>
    <br />
    <table width="80%%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
      <td class="groupTitle">Channels</td>
    </tr>
    <tr>
      <td>
  %(channels)s
  <form action="%(postURL)s" method="POST">
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
    <br />
    
    <table width="80%%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
      <td class="groupTitle">Webcast Service URL</td>
    </tr>
    <tr>
      <td bgcolor="white" width="100%%" valign="top" class="blacktext">
        <form action="%(saveWebcastServiceURL)s" method="POST">
          <input name="webcastServiceURL" value="%(webcastServiceURL)s"/>
          <input type="submit" name="submit" value="Save">
          <span>Used for forthcoming webcast display in event public pages.</span>
        </form>
      </td>
    </tr>
    </table>
    <br />
    <table width="80%%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
      <td class="groupTitle">Webcast Administrators list</td>
    </tr>
    <tr>
      <td bgcolor="white" width="100%%" valign="top" class="blacktext">
	%(adminList)s
      </td>
    </tr>
    </table>
  </td>
</tr>
</table>
<br /><br />
