$(document).ready(function() {
    // Header shrinking function
    $(window).scroll(function() {
        if (($(window).scrollTop() >= $('.init-setup-header').outerHeight()/2) &&
                !$('.init-setup-header').hasClass('mini')) {
            $('.init-setup-header').addClass('mini');
            $('.init-setup-body').addClass('mini');
            $(window).scrollTop(0);
        }
    });

    // Instance Tracking slider
    $('#form-group-enable_tracking .switch-input').on('change', function() {
        var $this = $(this);
        var enabled = $this.prop('checked');
        var itEmail = $('#contact_email');
        var itContact = $('#contact_name');
        var firstName = $('#first_name').val();
        var lastName = $('#last_name').val();
        var name = (!!firstName  && !!lastName) ? firstName + ' ' + lastName : '';

        itEmail.prop('required', enabled);
        itEmail.prop('disabled', !enabled);
        if (!itEmail.val()) {
            itEmail.val($('#email').val());
            itEmail.trigger('input');
        }
        itContact.prop('required', enabled);
        itContact.prop('disabled', !enabled);
        if (!itContact.val() && !!name) {
            itContact.val(name);
            itContact.trigger('input');
        }
    });
    $('#form-group-enable_tracking .switch-input').trigger('change');

    // Language selector
    $('.language-option').on('click', function setLanguage() {
        var currentLangInput = $('#language-hidden');
        var newLang = $(this).data('language-code');
        if (newLang !== currentLangInput.val()) {
            currentLangInput.val(newLang);
            $('#language-form').submit();
        }
    });
    $('#language-selector').dropdown();
});
