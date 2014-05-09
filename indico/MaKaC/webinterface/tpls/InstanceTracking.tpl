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
                    <a id="button-save" class="i-button disabled">Save</a>
                    <a id="button-cancel" class="i-button disabled">Cancel</a>
                </div>
            </div>
        </div>
        <div class="i-box titled out-of-sync">
            <div class="i-box-header">
                <div class="i-box-title">Data out of sync!</div>
            </div>
            <div class="i-box-content">
                <div class="missing-record-text">
                    <div>It seems like we lost your information on our server.</div>
                    <br>
                    <div>Click <strong>sync</strong> to send it again.</div>
                </div>
                <div class="out-of-sync-text">
                    <div>It seems like you changed some information lately and we still have the old version in our server.</div>
                    <br>
                    <div>The information out of sync are:</div>
                    <ul>
                        <div id="out-of-sync-url" class="out-of-sync-field">
                            <li>URL</li>
                            <span></span>
                        </div>
                        <div id="out-of-sync-contact" class="out-of-sync-field">
                            <li>Contact name</li>
                            <span></span>
                        </div>
                        <div id="out-of-sync-email" class="out-of-sync-field">
                            <li>Email</li>
                            <span></span>
                        </div>
                        <div id="out-of-sync-organisation" class="out-of-sync-field">
                            <li>Organisation</li>
                            <span></span>
                        </div>
                    </ul>
                    <div>Click <strong>sync</strong> to send them again.</div>
                </div>
                <input id="hidden-update-type" type="hidden" name="update_it_type" value="none">
                <div class="group">
                    <a id="button-sync" class="i-button">Sync</a>
                </div>
            </div>
        </div>
    </div>

</form>

<script type="text/javascript">

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
    $('input').on('input', function(){
        $('.group a').removeClass('disabled');
    });

    var hiddenUpdate = $('#hidden-update-type');
    var outOfSync = $(".out-of-sync");
    if (${ itEnabled }) {
        $.ajax({
            url: "${ updateURL }${ uuid }",
            type: "GET",
            dataType: "json",
            success: function(response){
                var fields = [
                    ['url', response.url, ${ url | n,j }],
                    ['contact', response.contact, ${ contact | n,j }],
                    ['email', response.email, ${ email | n,j }],
                    ['organisation', response.organisation, ${ organisation | n,j }]
                ];

                var ok = true;
                for (var i=0; i<=3; i++) {
                    if (fields[i][1] != fields[i][2]) {
                        $('#out-of-sync-' + fields[i][0]).show();
                        $('#out-of-sync-' + fields[i][0] + ' span').text(fields[i][1] + ' ➟ ' + fields[i][2]);
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
    }

    var hiddenButtonPressed = $('#hidden-button-pressed');
    var itForm = $('#it-form');
    $('#button-save').on('click', function(){
        if (! $(this).hasClass('disabled')) {
            hiddenButtonPressed.val('save');
            itForm.submit();
        }
    });
    $('#button-cancel').on('click', function(){
        if (! $(this).hasClass('disabled')) {
            itForm.submit();
        }
    });
    $('#button-sync').on('click', function(){
        if (! $(this).hasClass('disabled')) {
            hiddenButtonPressed.val('sync');
            itForm.submit();
        }
    });

</script>
