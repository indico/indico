<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
<form id="registrationForm" action=${ postURL } method="POST" onSubmit="return formSubmit(this);" enctype="multipart/form-data">
    <table width="80%" align="left" style="padding-left: 5px;">
        % if title:
        <tr>
            <td nowrap align="center" class="title" style="padding-bottom:20px;">${ title }</td>
        </tr>
        % endif
        <div ng-app="nd" ng-controller="AppCtrl">
            <div nd-reg-form conf-id="${confId}" edit-mode="false"></div>
            <input type="hidden" value="${confId}" id="conf_id">
        </div>
        <tr>
            <td class="regFormMandatoryInfo">
                <span>${ _("(All the fields marked with ") }</span>
                <span class="regFormMandatoryField">*</span>
                <span>${ _(" are mandantory)") }</span>
            </td>
        </tr>
        <tr>
            <td align="center" style="padding-bottom: 40px;">
                <input type="submit" class="regFormButton" value="Register">
            </td>
        </tr>
    </table>
    <br>
    </form>
    <input type="hidden" value="${confId}" id="conf_id">
    <script type="text/javascript">
        $("div#registrationForm").html(progressIndicator(false, true).dom);
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

        $(function() {
            var confId = ${ confId };
            //var rfView = new RegFormDisplayView({el : $("div#registrationForm")} ,confId );
            $(".regFormButton").click(function(){
                var self = this;
                new ConfirmPopup($T("Registration"),$T("Are you sure you want to submit this form?"), function(confirmed) {
                    if(confirmed) {
                        $(self).closest("form").submit();
                    }
                }).open();
                return false;
              });
          });
    </script>
</%block>
