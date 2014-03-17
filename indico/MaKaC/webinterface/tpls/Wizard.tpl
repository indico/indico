<% from indico.util.i18n import getLocaleDisplayNames %>
<style type="text/css">

    .titleCellTD {
        width: 20%;
    }

</style>

<form id="wizard-form" action="" method="POST">

    <div class="container" style="width: 100%; margin: 50px auto; max-width: 650px">
        <div class="groupTitle" style="margin-bottom: 30px; font-size: 25pt; white-space: nowrap;">
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
                                    <input class="wizardMandatoryField1" id="name" type="text" name="name" value=${ name } required style="width: 80%;">
                                </td>
                            </tr>
                            <tr>
                                <td class="titleCellTD">
                                    <span class="titleCellFormat">${ _("Family name")}</span>
                                </td>
                                <td class="contentCellTD">
                                    <input class="wizardMandatoryField1" id="surName" type="text" name="surName" value=${ surName } required style="width: 80%;">
                                </td>
                            </tr>
                            <tr>
                                <td class="titleCellTD">
                                    <span class="titleCellFormat">${ _("Email")}</span>
                                </td>
                                <td class="contentCellTD">
                                    <input class="wizardMandatoryField1" id="userEmail" type="email" name="userEmail" value=${ userEmail } required style="width: 50%;">
                                </td>
                            </tr>
                            <tr>
                                <td class="titleCellTD">
                                    <span class="titleCellFormat">${ _("Login")}</span>
                                </td>
                                <td class="contentCellTD">
                                    <input class="wizardMandatoryField1" id="login" type="text" name="login" value=${ login } required style="width: 30%;">
                                </td>
                            </tr>
                            <tr>
                                <td class="titleCellTD">
                                    <span class="titleCellFormat">${ _("Password")}</span>
                                </td>
                                <td class="contentCellTD">
                                    <input class="wizardMandatoryField1" id="password" type="password" name="password" value="" required style="width: 30%;">
                                </td>
                            </tr>
                            <tr>
                                <td class="titleCellTD">
                                        <span class="titleCellFormat">${ _("Password (again)")}</span>
                                </td>
                                <td class="contentCellTD">
                                    <input class="wizardMandatoryField1" id="passwordBis" type="password" name="passwordBis" value="" required style="width: 30%;">
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

            <div class="i-box titled" id="step2">
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
                                        <input class="wizardMandatoryField2" id="organisation" type="text" name="organisation" value=${organisation} required style="width: 70%;">
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

            <div class="i-box titled" id="step3">
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
                                        <input id="enable" type="checkbox" name="enable" value="${ _("checked")}" ${checked}>
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
        clicked[0] = true;
        var name = $('#name'),
                surName = $('#surName'),
                userEmail = $('#userEmail'),
                login = $('#login'),
                password = $('#password'),
                passwordBis = $('#passwordBis');

        var wrong = [];
        if (name.prop('validity').valueMissing){
            wrong.push(name);
        }
        if (surName.prop('validity').valueMissing){
            wrong.push(surName);
        }
        if (!userEmail.prop('validity').valid){
            wrong.push(userEmail);
        }
        if (login.prop('validity').valueMissing){
            wrong.push(login);
        }
        if (password.prop('validity').valueMissing){
            wrong.push(password);
        }
        if (password.val() != passwordBis.val()){
            wrong.push(passwordBis);
        }

        if (wrong.length > 0){
            popup.open();
            wrong.forEach(function(elem){
                elem.addClass("hasError");
            });
        }
        else{
            nextStep(1);
        }
    });

    $('#nextStep2').on('click', function(e){
        clicked[1] = true;
        var organisation = $('#organisation');

        var wrong = [];
        if (organisation.prop('validity').valueMissing){
            wrong.push(organisation);
        }

        if (wrong.length > 0){
            popup.open();
            wrong.forEach(function(elem){
                elem.addClass("hasError");
            });
        }
        else{
            nextStep(2);
        }
    });

    $('#submit-wizard').on('click', function(e){
        e.preventDefault();
        clicked[2] = true;
        var enable = $('#enable'),
                itEmail = $('#itEmail');

        var wrong = [];
        if (enable.prop('checked') && !itEmail.prop('validity').valid){
            wrong.push(itEmail);
        }

        if (wrong.length > 0){
            popup.open();
            wrong.forEach(function(elem){
                elem.addClass("hasError");
            });
        }
        else{
            $('#wizard-form').submit();
        }
    });

    $('#previousStep2').on('click', function(e){
        previousStep(2);
    });

    $('#previousStep3').on('click', function(e){
        previousStep(3);
    });

    $('.wizardMandatoryField1').on('input', function(e){
        if (clicked[0]){
            if (!this.validity.valid){
                $(this).addClass('hasError');
            }
            else{
                $(this).removeClass('hasError');
            }
        }
    });

    $('.wizardMandatoryField2').on('input', function(e){
        if (clicked[1]){
            if (!this.validity.valid){
                $(this).addClass('hasError');
            }
            else{
                $(this).removeClass('hasError');
            }
        }
    });

    $('#enable').on('change', function(e){
        var itEmail = $('#itEmail');

        itEmail.prop('required', this.checked);
        itEmail.prop('disabled', !this.checked);
        if (this.checked){
            itEmail.addClass('wizardMandatoryField3');
            if (clicked[2]){
                if (!itEmail.prop('validity').valid){
                    itEmail.addClass('hasError');
                }
                else{
                    itEmail.removeClass('hasError');
                }
            }
            $('.wizardMandatoryField3').on('input', function(e){
                if (clicked[2]){
                    if (!this.validity.valid){
                        $(this).addClass('hasError');
                    }
                    else{
                        $(this).removeClass('hasError');
                    }
                }
            });
        }
        else{
            itEmail.removeClass('wizardMandatoryField3 hasError');
        }
    }).trigger('change');

    $('#password, #passwordBis').on('input', function(e){
        var password = $('#password'),
                passwordBis = $('#passwordBis');

        if (clicked[0]){
            if (password.val() != passwordBis.val()) {
                passwordBis.addClass("hasError");
            }
            else{
                passwordBis.removeClass("hasError");
            }
        }
    });

    var LANGUAGES = ${getLocaleDisplayNames() | n,j}
    var nav_lang = navigator.language || navigator.userLanguage;
    nav_lang = nav_lang.split('-')[0];

    $.each(LANGUAGES, function(i, lang) {
        var lang_code = lang[0].split('_')[0];
        $("#lang").append('<option value="' + lang[0] + '"' + \
                                            (lang_code == nav_lang ? "selected" : "") + \
                                            '>' + lang[1] + '</option>');
    });

    toggleSection(2);
    toggleSection(3);
    $('#step2').css('border-bottom-width', '0px');
    $('#step3').css('border-bottom-width', '0px');

</script>
