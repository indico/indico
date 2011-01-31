<form action="" method="POST">

<script type="text/javascript">
  var validators = [];
  var parameterManager = new IndicoUtil.parameterManager();
  var addParam = parameterManager.add;
</script>

<table width="70%" align="center">
	<tr><td>&nbsp;</td></tr>
    <tr>
        <td nowrap class="title"><center><%= title %></center></td>
    </tr>
    <tr>
        <td colspan="2" align="left">
            <br><b><%= _("""Please, note that fields marked with <font color="red">*</font> are mandatory""")%></b><br>
        </td>
    </tr>
    <tr>
        <td><br></td>
    </tr>
    <tr>
        <td>
            <%= personalData %>
        </td>
    </tr>
    <%= otherSections %>
    <tr>
        <td><br></td>
    </tr>
    <tr>
        <td align="center" style="border-top: 2px solid #777777;padding-top:10px"><input type="button" class="btn" value="<%= _("register")%>"></td>
    </tr>
</table>
<br>
</form>