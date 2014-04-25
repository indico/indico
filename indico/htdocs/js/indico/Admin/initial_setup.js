$(document).ready(function(){
    var ok = true;
    var scrollDelay = 1000;
    var clicked = false;
    var fields = [[$('#name'), $('#surname'), $('#user-email'), $('#login'), $('#password'), $('#password-confirm')],
                  [$('#organisation')],
                  [$('#it-email')]];

    // Scroll the page to a step
    function scrollToStep(step){
        scrollToElem($('#step'+step));
    }

    // Scroll the page to a JQuery element
    function scrollToElem(elem){
        var miniHeaderHeight = 120;
        var headerPaddingTop = 20;
        var headerBorderBottom = 5;
        var stepWrapperPaddingTop = 75;
        var offset = miniHeaderHeight+headerPaddingTop+headerBorderBottom+stepWrapperPaddingTop
        $('html, body').animate({
            scrollTop: elem.offset().top -offset
        }, scrollDelay);
    }

    // Mark a field as valid
    function markValidField(field){
        field.removeClass('hasError');
    }

    // Mark a field as invalid
    function markInvalidField(field){
        field.addClass('hasError');
    }

    // Fill the contact email field with the personal email
    function fillITEmail(){
        var userEmail = $('#user-email');
        var itEmail = $('#it-email');
        var itEmailHidden = $('#it-email-hidden');
        if (itEmailHidden.val() == ''){
            itEmail.val(userEmail.val());
        } else{
            itEmail.val(itEmailHidden.val());
        }
    }

    // Empty the contact email field
    function emptyITEmail(){
        itEmail = $('#it-email');
        itEmail.val('');
    }

    // Validate all the steps
    function validateSteps(){
        ok = true;
        invalidStep = 0;
        for (var i=1; i<=3; i++){
            validateStep(i);
            if (!ok && invalidStep == 0){
                invalidStep = i;
            }
        }
        return invalidStep;
    }

    // Validate a single step
    function validateStep(step){

        for (var i=0; i<fields[step-1].length; i++){
            fields[step-1][i].trigger('input').trigger('hideTooltip');
        }
    }

    // Submit form
    $('#submit-initial-setup').on('click', function(e){
        e.preventDefault();
        clicked = true;
        var invalidStep = validateSteps();

        if (invalidStep == 0){
            $('#initial-setup-form').submit();
        } else{
            scrollToStep(invalidStep);
        }
    });

    // QTip setup
    $('#initial-setup-form input').qtip({
        content: {
            attr: 'data-error-tooltip'
        },
        position: {
            at: 'right center',
            my: 'left center'
        },
        show: {
            event: 'showTooltip'
        },
        hide: {
            event: 'hideTooltip'
        }
    }).on('focus input mouseenter', function(){
        if ($(this).hasClass('hasError')){
            $(this).trigger('showTooltip');
        }
        else{
            $(this).trigger('hideTooltip');
        }
    }).on('blur', function(){
        $(this).trigger('hideTooltip');
    });
    $('#initial-setup-form').on('mouseleave', 'input:not(:focus)', function(){
        $(this).trigger('hideTooltip');
    });

    // Header shrinking function
    $(window).scroll(function(){
        if (($(window).scrollTop() >= $('.init-setup-header').outerHeight()/2) && !$('.init-setup-header').hasClass('mini')) {
            $('.init-setup-header').addClass('mini');
            $('.init-setup-body').addClass('mini');
            $(window).scrollTop(0);
        }
    });

    // Instance Tracking slider
    $('.toggle-button').on('click', function() {
        $(this).toggleClass('toggled');
        var toggled = $(this).hasClass('toggled');
        var itEmail = $('#it-email');
        var checkbox = $('#enable');
        itEmail.prop('required', toggled);
        itEmail.prop('disabled', !toggled);
        checkbox.prop('checked', toggled);
        if (toggled){
            fillITEmail();
            itEmail.trigger('input');
        }
        else{
            emptyITEmail();
            markValidField(itEmail);
        }
    });
    if ($('#enable').prop('checked')){
        $('.toggle-button').trigger('click');
    }

    // Fields validation setup
    $('#initial-setup-form :input:not(#password-confirm)').on('input', function(){
        if (!this.validity.valid){
            if (this.id == 'user-email' || this.id == 'it-email'){
                if (this.validity.valueMissing){
                    $(this).qtip('option', 'content.attr', "data-error-tooltip");
                }
                else{
                    $(this).qtip('option', 'content.attr', "data-error-tooltip2");
                }
            }
            if (clicked){
                markInvalidField($(this));
            }
            ok = false;
        }
        else{
            markValidField($(this));
        }
    });
    $('#password, #password-confirm').on('input', function(){
        var password = $('#password'),
            passwordConfirm = $('#password-confirm');
        if (password.val() != passwordConfirm.val()) {
            if (clicked){
                markInvalidField(passwordConfirm);
            }
            ok = false;
        }
        else {
            markValidField(passwordConfirm);
        }
    });

    // Language selector
    $('#lang option').each(function(){
        var form = $('#language-form');
        var langHidden = $('#language-hidden');
        var code = this.value;
        var name = this.innerHTML;
        $('#'+code).on('click', function(){
            langHidden.val(code);
            form.submit()
        });
    });
    $('#language-selector').dropdown();

    // Listener to store IT Email value
    $('#it-email').on('input', function(){
        var itEmailHidden = $('#it-email-hidden');
        itEmailHidden.val(this.value);
    });

});
