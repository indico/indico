<div class="groupTitle"> ${ _("Instance Tracking settings") }</div>

<form id="it-form" action="${ postURL }" method="POST">
    <input id="hidden-button-pressed" type="hidden" name="button_pressed" value="none">

    <div>
        <div class="instance-tracking-settings">
            <div class="clearfix">
                <div class="field-label">
                    <label class="dataCaptionFormat status-label">${ _('Status') }</label>
                </div>
                <div class="field-input">
                    <input class="hidden-input" id="enable" type="checkbox" name="enable" value="1" ${ checked }>
                    <div class="toggle-button">
                        <div class="toggle"></div>
                    </div>
                </div>
            </div>
            <div class="clearfix">
                <div class="field-label">
                    <label class="dataCaptionFormat" for="contact">${ _("Contact person name") }</label>
                </div>
                <div class="field-input">
                    <input id="contact" type="text" name="contact" value="${ contact }" disabled>
                </div>
            </div>
            <div class="clearfix">
                <div class="field-label">
                    <label class="dataCaptionFormat" for="email">${ _("Contact email address") }</label>
                </div>
                <div class="field-input">
                    <input id="email" type="text" name="email" value="${ email }" disabled>
                </div>
            </div>
            <div class="clearfix">
                <div class="group">
                    <a id="button-save" class="i-button disabled" href="#">${ _('Save') }</a>
                    <a id="button-cancel" class="i-button disabled" href="#">${ _('Cancel') }</a>
                </div>
            </div>
        </div>
        <div class="i-box titled out-of-sync">
            <div class="i-box-header">
                <div class="i-box-title">${ _('Data out of sync!') }</div>
            </div>
            <div class="i-box-content">
                <div class="missing-record-text">
                    <div>${ _('It seems like we lost your information on our server.') }</div>
                    <br>
                </div>
                <div class="out-of-sync-text">
                    <div>${ _('It seems like you changed some information lately and we still have the old version in our server.') }</div>
                    <br>
                    <div>${ _('The information out of sync is:') }</div>
                    <ul>
                        <div id="out-of-sync-url" class="out-of-sync-field">
                            <li>${ _('URL') }</li>
                            <span></span>
                        </div>
                        <div id="out-of-sync-contact" class="out-of-sync-field">
                            <li>${ _('Contact name') }</li>
                            <span></span>
                        </div>
                        <div id="out-of-sync-email" class="out-of-sync-field">
                            <li>${ _('Email') }</li>
                            <span></span>
                        </div>
                        <div id="out-of-sync-organisation" class="out-of-sync-field">
                            <li>${ _('Organisation') }</li>
                            <span></span>
                        </div>
                    </ul>
                </div>
                <div>${ _('Click <strong>sync</strong> to send it again.') }</div>
                <input id="hidden-update-type" type="hidden" name="update_it_type" value="none">
                <div class="group">
                    <a id="button-sync" class="i-button" href="#">${ _('Sync') }</a>
                </div>
            </div>
        </div>
    </div>

</form>

<script>

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
        $('.group a').removeClass('disabled');
    });
    if ($('#enable').prop('checked')) {
        $('.toggle-button').toggleClass('toggled');
        var contact = $('#contact');
        var email = $('#email');
        contact.prop('disabled', false);
        email.prop('disabled', false);
    }
    $('input').on('input', function() {
        $('.group a').removeClass('disabled');
    });

    var hiddenUpdate = $('#hidden-update-type');
    var outOfSync = $(".out-of-sync");
    % if itEnabled:
        $.ajax({
            url: "${ updateURL }${ uuid }",
            type: "GET",
            dataType: "json",
            success: function(response){
                var fields = {
                    'url': ${ url | n,j },
                    'contact': ${ contact | n,j },
                    'email': ${ email | n,j },
                    'organisation': ${ organisation | n,j }
                };

                var ok = true;
                for (var key in fields) {
                    if (response[key] != fields[key]) {
                        $('#out-of-sync-' + key).show();
                        $('#out-of-sync-' + key + ' span').text(response[key] + ' ➟ ' + fields[key]);
                        ok = false;
                    }
                }

                if (!ok) {
                    hiddenUpdate.val("update");
                    $('.out-of-sync-text').show();
                    outOfSync.show();
                }
            },
            error: function(){
                hiddenUpdate.val("register");
                $('.missing-record-text').show();
                outOfSync.show();
            }
        });
    % endif

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
