<div class="groupTitle"> ${ _("Instance Tracking settings") }</div>

<form id="it-form" action="${ postURL }" method="POST">
    <input id="hidden-button-pressed" type="hidden" name="button_pressed" value="none">
    <input id="hidden-update-type" type="hidden" name="update_it_type" value="none">

    <div>

        <div class="instance-tracking-description">
            <h3>Let us know that you exist!</h3>
            Be part of the ever growing Indico community!<br>
            <br>
            Choose to receive updated news on latest releases (2-3 times per year) as well as important security warnings.<br>
            <br>
            The following data will be sent back to us:
            <ul>
                <li>Contact person</li>
                <li>Contact email</li>
                <li>Server URL</li>
                <li>Name of the organisation</li>
            </ul>
            Please note that <strong>no private information</strong> will ever be sent to the Indico Project and that you can disable it anytime.<br>
            <br>
            <div class="additional-description">
                Alongside to the previous information, the following data (strictly public) might be collected by us:
                <ul>
                    <li>Server default language</li>
                    <li>Indico version installed</li>
                    <li>Python version used</li>
                    <li>Statistics data (number of events, contributions, etc...)</li>
                </ul>
                It might happen that sometime your data will be out of sync with the data we have in our server.<br>
                When it happens you will be notified and you will be able to choose whether to sync it or not.
            </div>
        </div>

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
                    <label class="dataCaptionFormat" for="email">${ _("URL") }</label>
                </div>
                <div class="field-input">
                    <span>${ url }</span>
                    <i id="out-of-sync-url" class="icon-out-of-sync icon-warning"></i>
                </div>
            </div>
            <div class="clearfix">
                <div class="field-label">
                    <label class="dataCaptionFormat" for="email">${ _("Organisation") }</label>
                </div>
                <div class="field-input">
                    <span>${ organisation }</span>
                    <i id="out-of-sync-organisation" class="icon-out-of-sync icon-warning"></i>
                </div>
            </div>
            % if itEnabled:
                <div class="clearfix">
                    <div class="field-label">
                        <label class="dataCaptionFormat" for="email">${ _("Status") }</label>
                    </div>
                    <div id="sync-status" class="field-input">
                        <img src="${ Config.getInstance().getSystemIconURL('loading') }"/>
                    </div>
                </div>
            % endif
            <div class="toolbar clearfix">
                <div class="group">
                    <a id="button-sync" class="i-button disabled" href="#">
                        ${ _('Sync') }
                        <i class="icon-loop"></i>
                    </a>
                </div>
                <div id="save-cancel-group" class="group">
                    <a id="button-save" class="i-button disabled" href="#">
                        ${ _('Save') }
                        <i class="icon-disk"></i>
                    </a>
                    <a id="button-cancel" class="i-button disabled" href="#">
                        ${ _('Cancel') }
                        <i class="icon-close2"></i>
                    </a>
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
                        if (key != 'enabled') {
                            $('#out-of-sync-' + key).qtip({
                                content: {
                                    text: 'Value on server: \"' + response[key] + '\"'
                                },
                                position: {
                                    at: 'right center',
                                    my: 'left center'
                                }
                            });
                        }
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
                } else {
                    syncMessage.text('Synced!');
                    syncMessage.addClass('data-synced');
                }
            },
            error: function(){
                hiddenUpdate.val("register");
                $('#out-of-sync-enabled').show();
                $('#button-sync').removeClass('disabled');
                syncStatus.children('img').remove();
                $('<span>', {text: 'Out of sync!', class: 'data-out-of-sync'}).appendTo(syncStatus);
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
