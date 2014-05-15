<div class="groupTitle"> ${ _("Instance Tracking settings") }</div>

<div class="warning-message-box out-of-sync-popup">
    <div class="message-text">
        ${ _('It seems like your data is out of sync with the data we have in our server or an error occured during connection.') }<br>
        ${ _('You can choose here whether to sync it or not or just disable the Instance Tracking service.') }
    </div>
</div>

<form id="it-form" action="${ postURL }" method="POST">
    <input id="hidden-button-pressed" type="hidden" name="button_pressed" value="none">
    <input id="hidden-update-type" type="hidden" name="update_it_type" value="none">

    <div>

        <div class="instance-tracking-settings">
            <div class="clearfix">
                <div class="field-label">
                    <label class="dataCaptionFormat status-label">${ _('Enabled') }</label>
                </div>
                <div class="field-input">
                    <input class="hidden-input" id="enable" type="checkbox" name="enable" value="1" ${ checked }>
                    <div class="toggle-button">
                        <div class="toggle"></div>
                    </div>
                    <i id="out-of-sync-enabled" class="icon-out-of-sync icon-warning"></i>
                </div>
            </div>
            <div class="clearfix">
                <div class="field-label">
                    <label class="dataCaptionFormat" for="contact">${ _("Contact person name") }</label>
                </div>
                <div class="field-input">
                    <input id="contact" type="text" name="contact" value="${ contact }" disabled>
                    <i id="out-of-sync-contact" class="icon-out-of-sync icon-warning"></i>
                </div>
            </div>
            <div class="clearfix">
                <div class="field-label">
                    <label class="dataCaptionFormat" for="email">${ _("Contact email address") }</label>
                </div>
                <div class="field-input">
                    <input id="email" type="text" name="email" value="${ email }" disabled>
                    <i id="out-of-sync-email" class="icon-out-of-sync icon-warning"></i>
                </div>
            </div>
            <div class="clearfix">
                <div class="field-label">
                    <label class="dataCaptionFormat">${ _("URL") }</label>
                </div>
                <div class="field-input">
                    <span>${ url }</span>
                    <i id="out-of-sync-url" class="icon-out-of-sync icon-warning"></i>
                </div>
            </div>
            <div class="clearfix">
                <div class="field-label">
                    <label class="dataCaptionFormat">${ _("Organisation") }</label>
                </div>
                <div class="field-input">
                    <span>${ organisation }</span>
                    <i id="out-of-sync-organisation" class="icon-out-of-sync icon-warning"></i>
                </div>
            </div>
            % if itEnabled:
                <div class="clearfix">
                    <div class="field-label">
                        <label class="dataCaptionFormat">${ _("Status") }</label>
                    </div>
                    <div id="sync-status" class="field-input">
                        <img src="${ Config.getInstance().getSystemIconURL('loading') }"/>
                    </div>
                </div>
            % endif
            <div class="toolbar clearfix">
                <div class="group">
                    <a id="button-sync" class="i-button icon-loop disabled" href="#">${ _('Sync') }</a>
                </div>
                <div id="save-cancel-group" class="group">
                    <a id="button-save" class="i-button icon-disk disabled" href="#">${ _('Save') }</a>
                    <a id="button-cancel" class="i-button icon-close2 disabled" href="#">${ _('Cancel') }</a>
                </div>
            </div>
        </div>

        <div class="instance-tracking-description">
            <div class="info-message-box">
                <div class="message-text">
                    <h4>${ _('Let us know that you exist!') }</h4>
                    ${ _('By enabling this service you will receive updated news on latest releases as well as important security warnings.') }<br>
                    ${ _('The following data will be sent back to us:') }
                    <ul>
                        <li>${ _('Contact person') }</li>
                        <li>${ _('Contact email') }</li>
                        <li>${ _('Server URL') }</li>
                        <li>${ _('Name of the organisation') }</li>
                    </ul>
                    ${ _('Alongside the previous data, the following public information will be periodically collected by us:') }
                    <ul>
                        <li>${ _('Server default language') }</li>
                        <li>${ _('Indico version installed') }</li>
                        <li>${ _('Python version used') }</li>
                        <li>${ _('Statistical data (number of events, contributions, etc...)') }</li>
                    </ul>
                </div>
            </div>
        </div>

    </div>

</form>

<script>

    // Slider and input and buttons activation
    $('.toggle-button').on('click', function() {
        var $this = $(this);
        $this.toggleClass('toggled');
        var toggled = $this.hasClass('toggled');
        var checkbox = $('#enable');
        var contact = $('#contact');
        var email = $('#email');
        checkbox.prop('checked', toggled);
        contact.prop('disabled', !toggled);
        email.prop('disabled', !toggled);
        $('#save-cancel-group a').removeClass('disabled');
    });
    if ($('#enable').prop('checked')) {
        $('.toggle-button').toggleClass('toggled');
        var contact = $('#contact');
        var email = $('#email');
        contact.prop('disabled', false);
        email.prop('disabled', false);
    }
    $('input').on('input', function() {
        $('#save-cancel-group a').removeClass('disabled');
    });

    // Out of sync data
    % if itEnabled:
        var hiddenUpdate = $('#hidden-update-type');
        var outOfSync = $('.out-of-sync');
        var syncStatus = $('#sync-status');
        $.ajax({
            url: "${ updateURL }${ uuid }",
            type: "GET",
            dataType: "json",
            success: function(response){
                var fields = {
                    'url': ${ url | n,j },
                    'contact': ${ contact | n,j },
                    'email': ${ email | n,j },
                    'organisation': ${ organisation | n,j },
                    'enabled': ${ itEnabled | n,j }
                };

                var ok = true;
                for (var key in fields) {
                    if (response[key] != fields[key]) {
                        $('#out-of-sync-' + key).show();
                        $('#out-of-sync-' + key).qtip({
                            content: {
                                text: 'Value on server: \"' + response[key] + '\"'
                            },
                            position: {
                                at: 'right center',
                                my: 'left center'
                            }
                        });
                        ok = false;
                    }
                }

                syncStatus.children('img').remove();
                var syncMessage = $('<span>');
                syncMessage.appendTo(syncStatus);

                if (!ok) {
                    hiddenUpdate.val("update");
                    $('#button-sync').removeClass('disabled');
                    syncMessage.text('Out of sync!');
                    syncMessage.addClass('data-out-of-sync');
                    $('.out-of-sync-popup').show();
                } else {
                    syncMessage.text('Synced!');
                    syncMessage.addClass('data-synced');
                }
            },
            error: function(xhr, textStatus, errorThrown){
                $('.out-of-sync-popup').show();
                hiddenUpdate.val("register");
                syncStatus.children('img').remove();
                var syncMessage = $('<span>');
                syncMessage.appendTo(syncStatus);
                var syncIcon = $('<i>', {class: 'icon-out-of-sync icon-warning'});
                syncIcon.appendTo(syncStatus);
                syncIcon.show();
                code = xhr.status;
                if (code == 404) {
                    $('#button-sync').removeClass('disabled');
                    syncMessage.text('Out of sync!');
                    syncMessage.addClass('data-out-of-sync');
                    syncIcon.qtip({
                        content: {
                            text: 'Instance not found on server'
                        },
                        position: {
                            at: 'right center',
                            my: 'left center'
                        }
                    });
                } else {
                    syncMessage.text('Connection error!');
                    syncMessage.addClass('connection-error');
                    syncIcon.qtip({
                        content: {
                            text: 'AJAX request failed: ' + errorThrown
                        },
                        position: {
                            at: 'right center',
                            my: 'left center'
                        }
                    });
                }
            }
        });
    % endif

    // Buttons
    var hiddenButtonPressed = $('#hidden-button-pressed');
    var itForm = $('#it-form');
    $('#button-save').on('click', function(e){
        e.preventDefault();
        if (! $(this).hasClass('disabled')) {
            hiddenButtonPressed.val('save');
            itForm.submit();
        }
    });
    $('#button-cancel').on('click', function(e){
        e.preventDefault();
        if (! $(this).hasClass('disabled')) {
            itForm.submit();
        }
    });
    $('#button-sync').on('click', function(e){
        e.preventDefault();
        if (! $(this).hasClass('disabled')) {
            hiddenButtonPressed.val('sync');
            itForm.submit();
        }
    });

</script>
