<div ng-app="nd" ng-controller="AppCtrl">
    <div nd-reg-form conf-id="${confId}" edit-mode="true"></div>
    <input type="hidden" value="${confId}" id="conf_id">
</div>

<script>
    $(function(){
        $(window).scroll(function(){
            IndicoUI.Effect.followScroll();
        });
    });
</script>
