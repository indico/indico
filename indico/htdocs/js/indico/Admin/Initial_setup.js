$(document).ready(function(){
    var ok = true;
    var scrollDelay = 1000;
    var clicked = false;
    var fields = [[$('#name'), $('#surname'), $('#user_email'), $('#login'), $('#password'), $('#password_confirm')],
                  [$('#organisation')],
                  [$('#it_email')]];

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
        user_email = $('#user_email');
        it_email = $('#it_email');
        if (it_email.val() == ''){
            it_email.val(user_email.val());
        }
    }

    // Empty the contact email field
    function emptyITEmail(){
        it_email = $('#it_email');
        it_email.val('');
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
        var itEmail = $('#it_email');
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
    $('#initial-setup-form :input:not(#password_confirm)').on('input', function(){
        if (!this.validity.valid){
            if (this.id == 'user_email' || this.id == 'it_email'){
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
    $('#password, #password_confirm').on('input', function(){
        var password = $('#password'),
            password_confirm = $('#password_confirm');
        if (password.val() != password_confirm.val()) {
            if (clicked){
                markInvalidField(password_confirm);
            }
            ok = false;
        }
        else {
            markValidField(password_confirm);
        }
    });

    // Language selector
    var form = $('#languageForm');
    var inputHidden = $('#languageInputHidden');
    $('#lang option').each(function(){
        var code = this.value;
        var name = this.innerHTML;
        $('#'+code).on('click', function(){
            inputHidden.val(code);
            form.submit()
        });
    });
    $('#languageSelector').dropdown();

});
