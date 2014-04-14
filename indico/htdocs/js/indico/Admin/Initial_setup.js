$(document).ready(function(){
	var ok = true;

	function scrollToElem(elem){
	    $('html, body').animate({
	        scrollTop: elem.offset().top
	    }, 1000);
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
	            invalidField($(this));
	            ok = false;
	        }
	        else{
	            validField($(this));
	        }
	    }).trigger('input');
	    $('#password, #password_confirm').on('input', function(){
	        var password = $('#password'),
	            password_confirm = $('#password_confirm');
	        if (password.val() != password_confirm.val()) {
	            invalidField(password_confirm);
	            ok = false;
	        }
	        else {
	            validField(password_confirm);
	        }
	    }).trigger('input');
	    $('#initial-setup-form input').trigger('hideTooltip');

	    if (ok){
	    	user_email = $('#user_email');
	    	it_email = $('#it_email');
	    	if (it_email.val() == ''){
	    		it_email.val(user_email.val());
	    	}
		    scrollToElem($('#step2'));
	    }
	});

	$('#nextStep2').on('click', function(){
	    ok = true;
	    $('#step2 :input').on('input', function(){
	        if (!this.validity.valid){
	            invalidField($(this));
	            ok = false;
	        }
	        else{
	            validField($(this));
	        }
	    }).trigger('input');
	    $('#initial-setup-form input').trigger('hideTooltip');

	    if (ok){
		    scrollToElem($('#step3'));
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
	            invalidField(itEmail);
	            ok = false;
	        }
	        else{
	            validField(itEmail);
	        }
	    }
	    else{
	        validField(itEmail);
	    }
	}

	$('#previousStep2').on('click', function(){
	    scrollToElem($('#step1'));
	});

	$('#previousStep3').on('click', function(){
	    scrollToElem($('#step2'));
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
	}).trigger('change');

	function validField(field){
	    field.removeClass('hasError');
	}

	function invalidField(field){
	    field.addClass('hasError');
	}

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
});
