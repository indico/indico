<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
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
              new AlertPopup($T("Error"), $T("The form contains some errors. Please, correct them and submit again.")).open();
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
    <table width="70%" align="center">
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
                <input type="submit" class="regFormButton" value="${ _("Modify")}">
            </td>
        </tr>
    </table>
    <br>
    </form>
</%block>
