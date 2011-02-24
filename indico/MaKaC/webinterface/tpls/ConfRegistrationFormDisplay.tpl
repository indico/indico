<script>
  var validators = [];
  var parameterManager = new IndicoUtil.parameterManager();
  var addParam = parameterManager.add;

  function addValidator(validator) {
      validators.push(validator);
  }

  function enableAll(f) {
    for (i = 0; i < f.elements.length; i++) {
      f.elements[i].disabled=false
    }
  }

  function formSubmit(f) {
      if (!parameterManager.check()) {
          alert($T("The form contains some errors. Please, correct them and submit again."));
          return false;
      }

      for (var i in validators) {
          var validator = validators[i];
          if (!validator()) {
              return false;
          }
      }

      enableAll(f);
      return true;
  }
</script>

<form action=<%= postURL %> method="POST" onSubmit="return formSubmit(this);">
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
        <td align="center" class="regFormBottomLine"><input type="submit" class="btn" value="register" onClick="return confirm('<%= _("Are you sure you want to submit this form?") %>');"></td>
    </tr>
</table>
<br>
</form>