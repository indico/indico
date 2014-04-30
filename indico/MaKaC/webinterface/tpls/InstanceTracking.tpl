<div class="groupTitle"> ${ _("Instance Tracking settings") }</div>

<form action="${ postURL }" method="POST">

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
                <input id="contact" type="text" name="contact" value="${ contact }">
            </div>
        </div>
        <div class="clearfix">
            <div class="field-label">
                <label class="dataCaptionFormat" for="email">${ _("Contact email address") }</label>
            </div>
            <div class="field-input">
                <input id="email" type="text" name="email" value="${ email }">
            </div>
        </div>
        <div class="clearfix">
            <div class="buttons-group">
                <input type="submit" class="btn" name="save" value="${ _("Save")}" disabled>
                <input type="submit" class="btn" name="cancel" value="${ _("Cancel")}" disabled>
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
        checkbox.prop('checked', toggled);
        $('.buttons-group input').prop('disabled', false);
    });
    if ($('#enable').prop('checked')) {
        $('.toggle-button').toggleClass('toggled');
    }
    $('input').on('input', function(){
        $('.buttons-group input').prop('disabled', false);
    });
</script>
