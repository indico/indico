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
          new AlertPopup($T("Form Error"), $T("The form contains some errors. Please, correct them and submit again.")).open();
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

<form action=${ postURL } method="POST" onSubmit="return formSubmit(this);" enctype="multipart/form-data">
<br>
<table width="60%" align="center" style="border-left:1px solid #777777;border-top:1px solid #777777;" cellspacing="0">
  <tr>
    <td nowrap class="groupTitle" colspan="2"><b>${ _("Modifying") } ${ title }</b></td>
  </tr>
  <tr><td><br></td></tr>
  <tr>
    <td align="left" valign="top">
      <table>
        ${ fields }
      </table>
    </td>
  </tr>
  <tr><td>&nbsp;</td></tr>
  <tr>
    <td align="left" colspan="2">
      <input type="submit" class="btn" name="modify" value="${ _("modify")}">
      <input type="submit" class="btn" name="cancel" value="${ _("cancel")}">
    </td>
  </tr>
</table>
<br>
</form>
