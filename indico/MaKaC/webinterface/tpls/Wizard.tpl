<% from indico.util.i18n import getLocaleDisplayNames %>
<style type="text/css">

    .titleCellTD {
        width: 20%;
    }

</style>

<form id="wizard-form" action="" method="POST">

    <div class="i-box-container" style="width: 100%; margin: 50px auto; max-width: 650px">
        <div class="groupTitle">
                ${ _("Admin Creation Wizard")}
        </div>
        <div class="i-box-group vert glued">

            <div class="i-box titled" id="step1">
                <div class="i-box-header">
                    <div class="i-box-title">${ _("1. User creation")}</div>
                </div>
                <div>
                    <div class="i-box-content">
                        <table width="100%">
                            <tr>
                                <td class="titleCellTD">
                                    <span class="titleCellFormat">${ _("First name")}</span>
                                </td>
                                <td class="contentCellTD">
                                    <input id="name" type="text" name="name" data-error-tooltip="${ _("You must enter a name")}" value=${ name } required style="width: 80%;">
                                </td>
                            </tr>
                            <tr>
                                <td class="titleCellTD">
                                    <span class="titleCellFormat">${ _("Family name")}</span>
                                </td>
                                <td class="contentCellTD">
                                    <input id="surname" type="text" name="surname" data-error-tooltip="${ _("You must enter a surname")}" value=${ surname } required style="width: 80%;">
                                </td>
                            </tr>
                            <tr>
                                <td class="titleCellTD">
                                    <span class="titleCellFormat">${ _("Email")}</span>
                                </td>
                                <td class="contentCellTD">
                                    <input id="userEmail" type="email" name="userEmail" data-error-tooltip="${ _("You must enter an user email address")}" value=${ userEmail } required style="width: 80%;">
                                </td>
                            </tr>
                            <tr>
                                <td class="titleCellTD">
                                    <span class="titleCellFormat">${ _("Login")}</span>
                                </td>
                                <td class="contentCellTD">
                                    <input id="login" type="text" name="login" data-error-tooltip="${ _("You must enter a login")}" value=${ login } required style="width: 50%;">
                                </td>
                            </tr>
                            <tr>
                                <td class="titleCellTD">
                                    <span class="titleCellFormat">${ _("Password")}</span>
                                </td>
                                <td class="contentCellTD">
                                    <input id="password" type="password" name="password" data-error-tooltip="${ _("You must define a password")}" value="" required style="width: 50%;">
                                </td>
                            </tr>
                            <tr>
                                <td class="titleCellTD">
                                        <span class="titleCellFormat">${ _("Password (again)")}</span>
                                </td>
                                <td class="contentCellTD">
                                    <input id="passwordBis" type="password" name="passwordBis" data-error-tooltip="${ _("You must enter the same password twice")}" value="" required style="width: 50%;">
                                </td>
                            </tr>
                        </table>
                    </div>
                    <div class="i-box-footer">
                        <div class="group right">
                            <a id="nextStep1" class="i-button">
                                ${ _("Next step")}
                                <i class="icon-next"></i>
                            </a>
                        </div>
                    </div>
                </div>
            </div>

            <div class="i-box titled" id="step2" style="border-bottom-width: 0px;">
                <div class="i-box-header">
                    <div class="i-box-title">${ _("2. Server settings")}</div>
                </div>
                <div>
                    <div class="i-box-content">
                        <table width="100%">
                            <tr>
                                <td class="titleCellTD">
                                        <span class="titleCellFormat">${ _("Language")}</span>
                                </td>
                                <td class="contentCellTD">
                                    <select size=1 name="lang" id="lang">
                                    </select>
                                </td>
                            </tr>
                            <tr>
                                <td class="titleCellTD">
                                        <span class="titleCellFormat">${ _("Timezone")}</span>
                                </td>
                                <td class="contentCellTD">
                                        <select name="timezone">${ timezoneOptions }</select>
                                </td>
                            </tr>
                            <tr>
                                <td class="titleCellTD">
                                        <span class="titleCellFormat">${ _("Organisation")}</span>
                                </td>
                                <td class="contentCellTD">
                                        <input id="organisation" type="text" name="organisation" data-error-tooltip="${ _("You must enter the name of your organization")}" value=${organisation} required style="width: 70%;">
                                </td>
                            </tr>
                        </table>
                    </div>
                    <div class="i-box-footer">
                        <div class="group right">
                            <a id="previousStep2" class="i-button icon-prev">${ _("Previous step")}</a>
                            <a id="nextStep2" class="i-button">
                                ${ _("Next step")}
                                <i class="icon-next"></i>
                            </a>
                        </div>
                    </div>
                </div>
            </div>

            <div class="i-box titled" id="step3" style="border-bottom-width: 0px;">
                <div class="i-box-header">
                    <div class="i-box-title">${ _("3. Instance Tracking")}</div>
                </div>
                <div>
                    <div class="i-box-content">
                        <table width="100%">
                            <tr>
                                <td colspan="2">
                                    <font color="gray">
                                        ${_("By enabling the Instance Tracking Terms you accept:")}
                                        <ul>
                                            <li>${ _("sending anonymous statistic data to Indico@CERN;")}</li>
                                            <li>${ _("receiving security warnings from the Indico team;")}</li>
                                            <li>${ _("receiving a notification when a new version is released.")}</li>
                                        </ul>
                                        ${_("Please note that no private information will ever be sent to Indico@CERN and that you will be able to change the Instance Tracking settings anytime in the future (from Server Admin, General Settings).")}
                                    </font>
                                </td>
                            </tr>
                            <tr>
                                <td class="titleCellTD">
                                        <span class="titleCellFormat">${ _("Enable")}</span>
                                </td>
                                <td class="contentCellTD">
                                        <input id="enable" type="checkbox" name="enable" value="1" ${checked}>
                                </td>
                            </tr>
                            <tr>
                                <td class="titleCellTD">
                                        <span class="titleCellFormat">${ _("Email")}</span>
                                </td>
                                <td class="contentCellTD">
                                        <input id="itEmail" type="email" name="instanceTrackingEmail" data-error-tooltip="${ _("You must enter an email for Instance Tracking")}" value=${instanceTrackingEmail} style="width: 50%;">
                                </td>
                            </tr>
                        </table>
                    </div>
                    <div class="i-box-footer">
                        <div class="group right">
                            <a id="previousStep3" class="i-button icon-prev">${ _("Previous step")}</a>
                            <a id="submit-wizard" class="i-button">
                                ${ _("Submit")}
                                <i class="icon-checkmark"></i>
                            </a>
                        </div>
                    </div>
                </div>
            </div>

        </div>
    </div>
</form>

<script type='text/javascript'>

    var ok = true;

    function toggleSection(section){
        $('#step'+section+'>div.i-box-header').nextUntil('#step'+(section+1)+'>div.i-box-header').slideToggle(800);
    }

    function expandCollapse(expand, collapse){
        $('#step'+expand).css('border-bottom-width', '1px');
        toggleSection(expand);
        toggleSection(collapse);
        setTimeout(function(){
            $('#step'+collapse).css('border-bottom-width', '0px');
        }, 800);
    }

    function nextStep(current){
        expandCollapse(current+1, current);
    }

    function previousStep(current){
        expandCollapse(current-1, current);
    }

    $('#nextStep1').on('click', function(){
        ok = true;
        $('#step1 :input:not(#passwordBis)').on('input', function(){
            if (!this.validity.valid){
                if (this.id == 'userEmail'){
                    if (this.validity.valueMissing){
                        $(this).qtip('option', 'content.text', "${ _("You must enter an user email")}");
                    }
                    else{
                        $(this).qtip('option', 'content.text', "${ _("You must enter a valid user email")}");
                    }
                }
                invalidField($(this));
                ok = false;
            }
            else{
                validField($(this));
            }
        }).trigger('input');
        $('#password, #passwordBis').on('input', function(){
            var password = $('#password'),
                passwordBis = $('#passwordBis');
            if (password.val() != passwordBis.val()) {
                invalidField(passwordBis);
                ok = false;
            }
            else {
                validField(passwordBis);
            }
        }).trigger('input');
        $('#wizard-form input').trigger('hideTooltip');

        if (ok){
            nextStep(1);
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
        $('#wizard-form input').trigger('hideTooltip');

        if (ok){
            nextStep(2);
        }
    });

    $('#submit-wizard').on('click', function(e){
        e.preventDefault();

        ok = true;
        $('#enable').on('change', function(){
            updateITEmail();
        }).trigger('change');
        $('#itEmail').on('input', function(){
            updateITEmail();
        });

        if (ok){
            $('#wizard-form').submit();
        }
    });

    function updateITEmail(){
        var enable = $('#enable'),
            itEmail = $('#itEmail');
        itEmail.prop('required', enable.prop('checked'));
        itEmail.prop('disabled', !enable.prop('checked'));
        if (enable.prop('checked')){
            if (!itEmail.prop('validity').valid){
                if (itEmail.prop('validity').valueMissing){
                    itEmail.qtip('option', 'content.text', "${ _("You must enter an email for Instance Tracking")}");
                }
                else{
                    itEmail.qtip('option', 'content.text', "${ _("You must enter a valid email for Instance Tracking")}");
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
        previousStep(2);
    });

    $('#previousStep3').on('click', function(){
        previousStep(3);
    });

    var LANGUAGES = ${getLocaleDisplayNames() | n,j}
    var nav_lang = navigator.language || navigator.userLanguage;
    nav_lang = nav_lang.split('-')[0];

    $.each(LANGUAGES, function(i, lang) {
        var lang_code = lang[0].split('_')[0];
        $('<option>', {
            value: lang[0],
            selected: lang_code == nav_lang,
            text: lang[1]
        }).appendTo('#lang');
    });

    toggleSection(2);
    toggleSection(3);
    $('#enable').on('change', function(){
        var itEmail = $('#itEmail');
        itEmail.prop('required', this.checked);
        itEmail.prop('disabled', !this.checked);
    }).trigger('change');

    function validField(field){
        field.removeClass('hasError');
    }

    function invalidField(field){
        field.addClass('hasError');
    }

    $('#wizard-form input').qtip({
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
    $('#wizard-form').on('mouseleave', 'input:not(:focus)', function(){
        $(this).trigger('hideTooltip');
    });

</script>
