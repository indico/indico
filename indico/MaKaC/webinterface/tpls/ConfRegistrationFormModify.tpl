<script>
  function enableAll(f) {
    for (i = 0; i < f.elements.length; i++) {
      f.elements[i].disabled=false
    }
  }
</script>

<form action=%(postURL)s method="POST" onSubmit="enableAll(this);">
<table width="70%%" align="center">
	<tr><td>&nbsp;</td></tr>
    <tr>
        <td nowrap class="title"><center><%= _("Modification of your registration")%></center></td>
    </tr>
    <tr>
        <td><br></td>
    </tr>
    <tr>
        <td>
            %(personalData)s
        </td>
    </tr>
    %(otherSections)s
    <tr>
        <td><br></td>
    </tr>
    <tr>
        <td colspan="2" align="center">
            <br><b><%= _("""Please, note that fields marked with <font color="red">*</font> are mandatory""")%></b><br>
        </td>
    </tr>
    <tr>
        <td align="center" style="border-top: 2px solid #777777;padding-top:10px"><input type="submit" class="btn" value="<%= _("modify")%>"></td>
    </tr>
</table>
<br>
</form>
