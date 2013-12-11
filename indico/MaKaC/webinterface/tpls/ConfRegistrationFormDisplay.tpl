<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
    <div ng-app="nd" ng-controller="AppCtrl">
        <div nd-reg-form
            conf-id="${conf.getId()}"
            currency="${currency}"
            edit-mode="false"
            post-url='${postURL}'></div>
    </div>

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
            var confId = ${ conf.getId() };
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
