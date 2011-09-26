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

<form action=${ postURL } method="POST" onSubmit="return formSubmit(this);">
<table width="80%" align="left" style="padding-left: 5px;">
    % if title:
    <tr>
        <td nowrap align="center" class="title" style="padding-bottom:20px;">${ title }</td>
    </tr>
    % endif
    ${ otherSections }
    <tr>
        <td class="regFormMandatoryInfo">
            <span>${ _("(All the fields marked with ") }</span>
            <span class="regFormMandatoryField">*</span>
            <span>${ _(" are mandantory)") }</span>
        </td>
    </tr>
    <tr>
        <td align="center" style="padding-bottom: 40px;">
            <input type="submit" class="regFormButton" value="Register" onClick="return confirm('${ _("Are you sure you want to submit this form?") }');">
        </td>
    </tr>
</table>
<br>
</form>
