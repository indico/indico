
<div class="container" style="width: 100%; margin: 50px auto; max-width: 420px">

<div class="groupTitle" style="margin-bottom: 30px; font-size: 25pt; white-space: nowrap;">
    ${ _("Log in to Indico")}
</div>
<div id="cookiesEnabled" style="display:none; text-align:center; color:#881122; font-size:large; padding-bottom:15px" colspan="2">
    ${_("Please enable cookies in your browser!")}
</div>

% if isSSOLoginActive:
<form id="signInSSOForm" action="${ ssoURL }" method="POST">
    <input id="authId" type="hidden" name="authId" value="">
    % for auth in authenticators:
        % if auth.isSSOLoginActive():
            <a href="#" data-id="${ auth.getId() }" class="i-button highlight signin js-sso-submit">
                <span class="auth-id">${ _('Login with Single SignOn') }</span>
                <i class="login-arrow"></i>
            </a>
        % endif
    % endfor
</form>

<div class="titled-rule">
    ${_('Or')}
</div>
% endif

<div class="i-box">
    <div class="i-box-header">
        <div class="i-box-title">
            ${ _('Login') }
        </div>
    </div>
    <div class="i-box-body">
        <form name="signInForm" action=${ postURL } method="POST">
            <input type="hidden" name="returnURL" value=${ returnURL }>
            <table>
                % if 'passwordChanged' in _request.args:
                <tr>
                    <td class="titleCellTD">&nbsp;</td>
                    <td class="contentCellTD">
                        <em>${ _("You may now log in using your new password") }</em>
                    </td>
                </tr>
                % endif
                <tr>
                    <td class="titleCellTD">
                        <span class="titleCellFormat">${ _('Username') }</span>
                    </td>
                    <td class="contentCellTD" id="usernameInput">
                        <input type="text" name="login" style="width: 100%;" value=${ login }>
                    </td>
                </tr>
                <tr>
                    <td class="titleCellTD">
                        <span class="titleCellFormat">${ _('Password') }</span>
                    </td>
                    <td class="contentCellTD" id="passwordInput">
                        <input type="password" name="password" style="width: 100%;">
                    </td>
                </tr>
                % if hasExternalAuthentication:
                <tr>
                    <td class="titleCellTD">&nbsp;</td>
                    <td class="contentCellTD">
                        <em>${_("Please note you can use your external") + " (%s) "%", ".join(externalAuthenticators)  + _("account")}</em>
                    </td>
                </tr>
                % endif
                % if msg:
                    <tr>
                        <td class="titleCellTD">&nbsp;</td>
                        <td class="contentCellTD">
                            <span style="color: darkred">${ msg }</span>
                        </td>
                    </tr>
                % endif
                <tr>
                    <td colspan="2">
                        <input type="submit"
                            id="loginButton"
                            value="${ _('Login') }"
                            class="i-button highlight right"/>
                    </td>
                </tr>
            </table>
        </form>
    </div>
</div>

<div style="margin-top: 20px;">
    <div style="padding: 5px 0; color: #444">
        % if isAuthorisedAccountCreation:
            ${_("If you don't have an account, you can create one")} <a href="${createAccountURL}">${_("here")}</a>
        % endif
    </div>
    <div style="color: #444">
        ${ _("Forgot your password?") } <span class="fakeLink" onclick="$('#reset_password').show(); $(this).hide();">${ ("Click here") }</span>
    </div>
    <div id="reset_password" style="padding: 5px 0; display:none">
        <form action=${ forgotPasswordURL } method="POST">
            <input type="text" name="email" placeholder="${_('enter your email address')}" style="width: 50%">
            <input type="submit" class="btn" value="${ _("Reset my password")}">
        </form>
    </div>
</div>

</div>
<script type="text/javascript">
    // Check whether cookies enabled
    document.cookie = "Enabled=true";
    // if retrieving the VALUE we just set actually works
    // then we know cookies enabled
    if (document.cookie.indexOf("Enabled=true") == -1) $("#cookiesEnabled").show();

    document.signInForm.login.focus();

    $('.js-sso-submit').on('click', function(e) {
        e.preventDefault();
        $('#authId').val($(this).data('id'));
        $('#signInSSOForm').submit();
    });
</script>
