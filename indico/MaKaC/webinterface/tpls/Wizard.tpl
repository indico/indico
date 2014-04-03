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
                                    <input id="name" type="text" name="name" value=${ name } required style="width: 80%;">
                                </td>
                            </tr>
                            <tr>
                                <td class="titleCellTD">
                                    <span class="titleCellFormat">${ _("Family name")}</span>
                                </td>
                                <td class="contentCellTD">
                                    <input id="surName" type="text" name="surName" value=${ surName } required style="width: 80%;">
                                </td>
                            </tr>
                            <tr>
                                <td class="titleCellTD">
                                    <span class="titleCellFormat">${ _("Email")}</span>
                                </td>
                                <td class="contentCellTD">
                                    <input id="userEmail" type="email" name="userEmail" value=${ userEmail } required style="width: 50%;">
                                </td>
                            </tr>
                            <tr>
                                <td class="titleCellTD">
                                    <span class="titleCellFormat">${ _("Login")}</span>
                                </td>
                                <td class="contentCellTD">
                                    <input id="login" type="text" name="login" value=${ login } required style="width: 30%;">
                                </td>
                            </tr>
                            <tr>
                                <td class="titleCellTD">
                                    <span class="titleCellFormat">${ _("Password")}</span>
                                </td>
                                <td class="contentCellTD">
                                    <input id="password" type="password" name="password" value="" required style="width: 30%;">
                                </td>
                            </tr>
                            <tr>
                                <td class="titleCellTD">
                                        <span class="titleCellFormat">${ _("Password (again)")}</span>
                                </td>
                                <td class="contentCellTD">
                                    <input id="passwordBis" type="password" name="passwordBis" value="" required style="width: 30%;">
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
                                        <input id="organisation" type="text" name="organisation" value=${organisation} required style="width: 70%;">
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
                                        <input id="itEmail" type="email" name="instanceTrackingEmail" value=${instanceTrackingEmail} style="width: 50%;">
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

    var popup = new WarningPopup('${ _("Form validation")}', "${ _("Some fields are invalid. Please, correct them and submit the form again.")}");
    var clicked = [false, false, false];
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

    $('#nextStep1').on('click', function(e){
        ok = true;
        $('#step1 :input:not(#passwordBis)').on('input', function(e){
            if (!this.validity.valid){
                $(this).addClass('hasError');
                ok = false;
            }
            else{
                $(this).removeClass('hasError');
            }
        }).trigger('input');
        $('#password, #passwordBis').on('input', function(e){
            var password = $('#password'),
                passwordBis = $('#passwordBis');
            if (password.val() != passwordBis.val()) {
                passwordBis.addClass("hasError");
                ok = false;
            }
            else {
                passwordBis.removeClass("hasError");
            }
        }).trigger('input');

        if (!ok){
            popup.open();
        }
        else{
            nextStep(1);
        }
    });

    $('#nextStep2').on('click', function(e){
        ok = true;
        $('#step2 :input').on('input', function(e){
            if (!this.validity.valid){
                $(this).addClass('hasError');
                ok = false;
            }
            else{
                $(this).removeClass('hasError');
            }
        }).trigger('input');

        if (!ok){
            popup.open();
        }
        else{
            nextStep(2);
        }
    });

    $('#submit-wizard').on('click', function(e){
        e.preventDefault();

        ok = true;
        $('#enable').on('change', function(e){
            updateITEmail();
        }).trigger('change');
        $('#itEmail').on('input', function(e){
            updateITEmail();
        });

        if (!ok){
            popup.open();
        }
        else{
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
                itEmail.addClass('hasError');
                ok = false;
            }
            else{
                itEmail.removeClass('hasError');
            }
        }
        else{
            itEmail.removeClass('hasError');
        }
    }

    $('#previousStep2').on('click', function(e){
        previousStep(2);
    });

    $('#previousStep3').on('click', function(e){
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
    $('#enable').on('change', function(e){
        var itEmail = $('#itEmail');
        itEmail.prop('required', this.checked);
        itEmail.prop('disabled', !this.checked);
    }).trigger('change');

</script>
