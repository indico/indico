<div class="groupTitle"> ${ _("Instance Tracking settings") }</div>

<form action="${ postURL }" method="POST">

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
                <div class="buttons-group">
                    <input type="submit" class="btn" name="save" value="${ _("Save")}" disabled>
                    <input type="submit" class="btn" name="cancel" value="${ _("Cancel")}" disabled>
                </div>
            </div>
        </div>
        <div class="out-of-sync">
            <div>Some of your Instance Tracking data seems to be out of sync.</div>
            <div>Do you want to update these information on the server?</div>
            <input id="hidden-update-type" type="hidden" name="update-it-type" value="none"></input>
            <div class="buttons-group">
                <input type="submit" class="btn" name="update" value="${ _("Update")}">
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
        $('.buttons-group input').prop('disabled', false);
    });
    if ($('#enable').prop('checked')) {
        $('.toggle-button').toggleClass('toggled');
        var contact = $('#contact');
        var email = $('#email');
        contact.prop('disabled', false);
        email.prop('disabled', false);
    }
    $('input').on('input', function(){
        $('.buttons-group input').prop('disabled', false);
    });

    var hiddenUpdate = $('#hidden-update-type');
    var outOfSync = $(".out-of-sync");
    if (${ itEnabled }) {
        $.ajax({
            url: "${ updateURL }${ uuid }",
            type: "GET",
            dataType: "json",
            success: function(response){
                var url = ${ url | n,j };
                var contact = ${ contact | n,j };
                var email = ${ email | n,j };
                var organisation = ${ organisation | n,j };

                if (url != response.url || contact != response.contact || email != response.email || organisation != response.organisation) {
                    hiddenUpdate.val("update");
                    outOfSync.css('display', 'block');
                }
            },
            error: function(){
                hiddenUpdate.val("register");
                outOfSync.css('display', 'block');
            }
        });
    }
</script>
