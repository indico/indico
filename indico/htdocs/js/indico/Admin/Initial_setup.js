$(document).ready(function(){
    var ok = true;
    var scrollDelay = 1000;
    var clicked = [false, false, false];
    var current = 1;
    var fields = [[$('#name'), $('#surname'), $('#user_email'), $('#login'), $('#password'), $('#password_confirm')],
                  [$('#organisation')],
                  [$('#it_email')]];

    function scrollToStep(step){
        ok = true;
        if (step > current){
            for (var i=0; i<fields[current-1].length; i++){
                fields[current-1][i].trigger('input').trigger('hideTooltip');
            }
        }
        if (step!=current && ok){
            uncheckTrackers();
            scrollToElem($('#step'+step));
            window.setTimeout(function(){
                uncheckTrackers();
                checkTracker(step);
            }, scrollDelay);
            current = step;
        }
    }

    function scrollToElem(elem){
        $('html, body').animate({
            scrollTop: elem.offset().top
        }, scrollDelay);
    }

    function checkTracker(step){
        var icon = $('#tracker'+ step +' i');
        icon.removeClass('black-icon').addClass('light-blue-logo-icon');
        if (!clicked[step-1]){
            icon.on('click', function(){
                scrollToStep(step);
            });
            clicked[step-1] = true;
        }
    }

    function uncheckTrackers(){
        var icons = $('.step-tracker div i');
        icons.removeClass('light-blue-logo-icon').addClass('black-icon');
    }

    function markValidField(field){
        field.removeClass('hasError');
    }

    function markInvalidField(field){
        field.addClass('hasError');
    }

    function updateITEmail(){
        var enable = $('#enable'),
            itEmail = $('#it_email');
        itEmail.prop('required', enable.prop('checked'));
        itEmail.prop('disabled', !enable.prop('checked'));
        if (enable.prop('checked')){
            if (!itEmail.prop('validity').valid){
                if (itEmail.prop('validity').valueMissing){
                    itEmail.qtip('option', 'content.attr', "data-error-tooltip");
                }
                else{
                    itEmail.qtip('option', 'content.attr', "data-error-tooltip2");
                }
                markInvalidField(itEmail);
                ok = false;
            }
            else{
                markValidField(itEmail);
            }
        }
        else{
            markValidField(itEmail);
        }
    }

    function fillITEmail(){
        user_email = $('#user_email');
        it_email = $('#it_email');
        if (it_email.val() == ''){
            it_email.val(user_email.val());
        }
    }

    function emptyITEmail(){
        it_email = $('#it_email');
        it_email.val('');
    }

    $('#nextStep1').on('click', function(){
        ok = true;
        $('#step1 :input:not(#password_confirm)').on('input', function(){
            if (!this.validity.valid){
                if (this.id == 'user_email'){
                    if (this.validity.valueMissing){
                        $(this).qtip('option', 'content.attr', "data-error-tooltip");
                    }
                    else{
                        $(this).qtip('option', 'content.attr', "data-error-tooltip2");
                    }
                }
                markInvalidField($(this));
                ok = false;
            }
            else{
                markValidField($(this));
            }
        }).trigger('input');
        $('#password, #password_confirm').on('input', function(){
            var password = $('#password'),
                password_confirm = $('#password_confirm');
            if (password.val() != password_confirm.val()) {
                markInvalidField(password_confirm);
                ok = false;
            }
            else {
                markValidField(password_confirm);
            }
        }).trigger('input');
        $('#initial-setup-form input').trigger('hideTooltip');

        if (ok){
            scrollToStep(2);
        }
    });

    $('#nextStep2').on('click', function(){
        ok = true;
        $('#step2 :input').on('input', function(){
            if (!this.validity.valid){
                markInvalidField($(this));
                ok = false;
            }
            else{
                markValidField($(this));
            }
        }).trigger('input');
        $('#initial-setup-form input').trigger('hideTooltip');

        if (ok){
            scrollToStep(3);
        }
    });

    $('#submit-initial-setup').on('click', function(e){
        e.preventDefault();

        ok = true;
        $('#enable').on('change', function(){
            updateITEmail();
        }).trigger('change');
        $('#itEmail').on('input', function(){
            updateITEmail();
        });

        if (ok){
            $('#initial-setup-form').submit();
        }
    });

    $('#previousStep2').on('click', function(){
        scrollToStep(1);
    });

    $('#previousStep3').on('click', function(){
        scrollToStep(2);
    });

    var nav_lang = navigator.language || navigator.userLanguage;
    nav_lang = nav_lang.split('-')[0];
    $('#lang option').each(function() {
        var lang_code = this.value.split('_')[0];
        if (lang_code == nav_lang){
            $('#lang').val(this.value);
            return false;
        }
    });

    $('#enable').on('change', function(){
        var itEmail = $('#it_email');
        itEmail.prop('required', this.checked);
        itEmail.prop('disabled', !this.checked);
        if (this.checked){
            fillITEmail();
        }
        else{
            emptyITEmail();
        }
    }).trigger('change');

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

    scrollToElem($('#step1'));
    checkTracker(1);

    for (var i=1; i<=3; i++){
        var icon = $('#tracker'+ i +' i');
        var stepTitle = $('#step'+ i +' div.step-container div.step-description div.step-title')
        icon.qtip({
            content: {
                text: stepTitle.text()
            },
            position: {
                at: 'right center',
                my: 'left center'
            }
        });
    }
});
