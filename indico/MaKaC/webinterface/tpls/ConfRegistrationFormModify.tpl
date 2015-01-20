<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
    <div ng-app="nd" ng-controller="AppCtrl">
        <div nd-reg-form
            conf-id="${conf.getId()}"
            conf-sections="${sections | n, j, h}"
            conf-currency="${currency}"
            post-url='${postURL}'
            update-mode="true"></div>
    </div>
</%block>
