<script>
  function enableAll(f) {
    for (i = 0; i < f.elements.length; i++) {
      f.elements[i].disabled=false
    }
  }
</script>

<form action=%(postURL)s method="POST" onSubmit="enableAll(this);">
<br>
<table width="60%%" align="center" style="border-left:1px solid #777777;border-top:1px solid #777777;" cellspacing="0">
  <tr>
    <td nowrap class="groupTitle" colspan="2"><b><%= _("Modifying")%> %(title)s</b></td>
  </tr>
  <tr><td><br></td></tr>
  <tr>
    <td align="left" valign="top">&nbsp;&nbsp;%(fields)s</td>
  </tr>
  <tr><td>&nbsp;</td></tr>
  <tr>
    <td align="left" colspan="2">
      <input type="submit" class="btn" name="modify" value="<%= _("modify")%>">
      <input type="submit" class="btn" name="cancel" value="<%= _("cancel")%>">
    </td>
  </tr>
</table>
<br>
</form>
