<div ng-app="nd" ng-controller="AppCtrl">
    <div nd-reg-form
        conf-id="${conf.getId()}"
        conf-sections="${sections | n, j, h}"
        conf-sdate="${conf.getStartDate()}"
        conf-edate="${conf.getEndDate()}"
        conf-currency="${currency}"
        edit-mode="true"></div>
    <input type="hidden" value="${conf.getId()}" id="conf_id">
</div>

<script>
    $(function(){
        $(window).scroll(function(){
            IndicoUI.Effect.followScroll();
        });
    });
</script>
