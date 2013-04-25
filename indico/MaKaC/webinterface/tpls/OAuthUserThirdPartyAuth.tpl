% if tokens:
<ol class="ordered-list" style="border-top: 1px solid #DDDDDD">
    % for token in tokens:
    <li>
        <div class="list-item-title">
            ${token.getConsumer().getName()}
            <div data-third-party-app="${token.getConsumer().getName()}" aria-hidden="true" style="margin:0" class="i-button i-button-mini icon-remove icon-only right"></div>
        </div>
        % if currentUser.isAdmin():
        <div class="list-item-content">
            <span class="list-item-content-title">${_("Access Token")}</span>
            <span class="list-item-content-data">${token.getId()}</span>
        </div>
        <div class="list-item-content">
            <span class="list-item-content-title">${_("Token secret")}</span>
            <span class="list-item-content-data">${token.getToken().secret}</span>
        </div>
        % endif
        <div class="list-item-content">
            <span class="list-item-content-title">${_("Last update")}</span>
            <span class="list-item-content-data">${formatTimestamp(token.getTimestamp())}</span>
        </div>
    </li>
    % endfor
</ol>
% endif

<h4 id="no_third_apps" style="display:none">${_("No third party application authorized yet.")}</h4>

<script type="text/javascript">

$(function() {
    % if not tokens:
        $("#no_third_apps").show();
    % endif
});
$("body").on("click",".icon-remove", function(){
    var self = $(this);
    var killProgress = IndicoUI.Dialogs.Util.progress($T("Deleting..."));
    jsonRpc(Indico.Urls.JsonRpcService, "oauth.unauthorizeConsumer" ,
            {'third_party_app': self.data("third-party-app"),
             'userId': '${user.getId()}'},
            function(result, error){
                if (exists(error)) {
                    killProgress();
                    IndicoUtil.errorReport(error);
                } else {
                    killProgress();
                    self.closest("li").remove();
                    if($(".ordered-list").prop("childElementCount").length==0){
                        $("#no_third_apps").show();
                    }
                }
            });
});

</script>