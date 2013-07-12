
<div class="container" style="width: 100%; margin: 50px auto; max-width: 420px">

<div class="groupTitle" style="margin-bottom: 30px; font-size: 25pt; white-space: nowrap;">${ _("Log in to Indico")}</div>
<div id="cookiesEnabled" style="display:none; text-align:center; color:#881122; font-size:large; padding-bottom:15px" colspan="2">
    ${("Please enable cookies in your browser!")}
</div>
% if isSSOLoginActive:
<div style="margin:10px auto;color:#444;font-size:14px">
    <div>${_("You can login through SSO:")}</div>
    <form name="signInSSOForm" action=${ ssoURL } method="POST">
    <div style="text-align:center;margin:10px">
        % for auth in authenticators:
            % if auth.isSSOLoginActive():
                <input type="submit" id="loginButton" value="${ auth.getId()}" name="authId">
            % endif
        % endfor
    </div>
    </form>
    <div>${_("or you can enter your credentials in the following form:")}</div>
</div>

% endif

<form name="signInForm" action=${ postURL } method="POST">
<input type="hidden" name="returnURL" value=${ returnURL }>

<table style="border: 1px solid #DDDDDD; padding: 20px; margin:auto; border-radius:6px">
    % if 'passwordChanged' in _request.args:
        <tr>
            <td class="titleCellTD">&nbsp;</td>
            <td class="contentCellTD">
                <em>${_("You may now log in using your new password")}</em>
            </td>
        </tr>
    % endif
    <tr>
        <td class="titleCellTD">
            <span class="titleCellFormat">${ _("Login")}</span>
        </td>
        <td class="contentCellTD" id="usernameInput">
            <input type="text" name="login" style="width: 99%;" value=${ login }>
        </td>
    </tr>
    <tr>
        <td class="titleCellTD">
            <span class="titleCellFormat">${ _("Password")}</span>
        </td>
        <td class="contentCellTD" id="passwordInput">
            <input type="password" name="password" style="width: 99%;">
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
        <td class="titleCellTD">&nbsp;</td>
        <td class="contentCellTD">
            <div class="i-buttons">
                <input type="submit" id="loginButton" class="i-button right" value="${ _("Login")}" name="signIn">
            </div>
        </td>
    </tr>
</table>
</form>
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
</script>
