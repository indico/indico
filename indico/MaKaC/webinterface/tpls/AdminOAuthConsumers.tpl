<div id="inPlaceAddConsumer" style="margin-bottom: 1em;"></div>
<ol class="ordered-list consumer-list" style="border-top: 1px solid #DDDDDD; margin-left: 0.25em">
    % for consumer in consumers:
    <li>
        <div class="list-item-title">
            ${consumer.getName()}
            <div data-consumer-key="${consumer.getId()}" aria-hidden="true" style="margin:0" class="i-button i-button-mini icon-remove icon-only right" title="${_("Delete this consumer.")}"></div>
            <div data-consumer-key="${consumer.getId()}" aria-hidden="true" style="margin:0" class="i-button i-button-mini icon-trust ${'trusted' if consumer.isTrusted() else ''} icon-only right"></div>
        </div>

        <div class="list-item-content">
            <span class="list-item-content-title">${_("Consumer key")}</span>
            <span class="list-item-content-data">${consumer.getId()}</span>
        </div>
        <div class="list-item-content">
            <span class="list-item-content-title">${_("Consumer secret")}</span>
            <span class="list-item-content-data">${consumer.getSecret()}</span>
        </div>
    </li>
    % endfor
</ol>

<script type="text/javascript">

function addHandler(result){
    var consumerItem = $('<li/>');
    var title = $("<div class='list-item-title'>{0}</div>".format(result["name"]));
    title.append($('<div data-consumer-key="{0}" aria-hidden="true" style="margin:0" class="i-button i-button-mini icon-remove icon-only right"></div>'.format(result["id"])));
    title.append($('<div data-consumer-key="{0}" aria-hidden="true" style="margin:0" class="i-button i-button-mini icon-trust icon-only right"></div>'.format(result["id"])));
    consumerItem.append(title);
    consumerItem.append('<div class="list-item-content"><span class="list-item-content-title">{0}</span><span class="list-item-content-data">{1}</span></div>'.format($T("Consumer key"), result["id"]));
    consumerItem.append('<div class="list-item-content"><span class="list-item-content-title">{0}</span><span class="list-item-content-data">{1}</span></div>'.format($T("Consumer secret"), result["secret"]));
    $(".ordered-list").append(consumerItem);
}

$(function() {
    $("#inPlaceAddConsumer").html(new AddItemWidget("consumer_name", "oauth.addConsumer", addHandler).draw());

    $("body").on("click", ".icon-remove", function() {
        var self = $(this);

        new ConfirmPopup($T("Delete consumer"), $T("Do you want to delete this consumer? Please note that this action cannot be undone."), function(confirmed) {
            if (!confirmed) {
                return;
            }

            var killProgress = IndicoUI.Dialogs.Util.progress($T("Deleting..."));
            jsonRpc(Indico.Urls.JsonRpcService, "oauth.removeConsumer",
                    {'consumer_key': self.data("consumer-key")},
                    function(result, error) {
                        if (exists(error)) {
                            killProgress();
                            IndicoUtil.errorReport(error);
                        } else {
                            killProgress();
                            self.closest("li").remove();
                        }
                    });
        }).open();
    });

    $("body").on("click",".icon-trust, .icon-untrust", function(){
        var self = $(this);
        var killProgress = IndicoUI.Dialogs.Util.progress($T("Saving..."));
        jsonRpc(Indico.Urls.JsonRpcService, "oauth.toogleCosumerTrusted" ,
                {'consumer_key': self.data("consumer-key")},
                function(result, error){
                    if (exists(error)) {
                        killProgress();
                        IndicoUtil.errorReport(error);
                    } else {
                        killProgress();
                        if(result ==false){
                            self.removeClass("trusted");
                        } else {
                            self.addClass("trusted");
                        }
                    }
                });
    });

    $('.consumer-list').on('mouseover', '.icon-trust', function(event) {
        $(this).qtip({
            content: {
                text: function() {
                    if ($(this).hasClass('trusted')) {
                        return $T("The consumer is trusted. That means that every time a user asks for the token the consumer will have access to the user events without asking for permission.");
                    }
                    return $T("The consumer is not trusted. That means that every time a user asks for the token an acceptance form will appear in order to give access to the application to get its events.");
                }
            },
            overwrite: false,
            show: {
                ready: true,
                event: event.type
            }
        });
    });
})
</script>
