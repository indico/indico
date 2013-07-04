
<div class="container" style="width: 100%; margin: 50px auto; max-width: 600px">

<div class="groupTitle" style="margin-bottom: 30px; font-size: 25pt;    ">${ _("Log in to Indico")}</div>
<div id="cookiesEnabled" style="display:none; text-align:center; color:#881122; font-size:large; padding-bottom:15px" colspan="2">
    ${("Please enable cookies in your browser!")}
</div>
% if isSSOLoginActive:
<div style="width:80%; margin:10px auto;color:#444;font-size:14px">
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

<table style="border: 1px solid #DDDDDD; padding: 20px; margin:auto; width:80%; border-radius:6px">
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
            <input type="text" name="login" size="20" value=${ login }>
        </td>
    </tr>
    <tr>
        <td class="titleCellTD">
            <span class="titleCellFormat">${ _("Password")}</span>
        </td>
        <td class="contentCellTD" id="passwordInput">
            <input type="password" name="password" size="20">
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
<div style="margin: 20px 30px 0 30px;">

    <table width="100%" cellspacing="5" cellpadding="0"><tbody>
        <tr>
            <td align="left"><img src="${ itemIcon }" alt="o" style="padding-right: 10px;"></td>
            <td align="left" width="100%">
                <div style="padding: 5px 0; color: #444">
                    % if isAuthorisedAccountCreation:
                        ${_("If you don't have an account, you can create one")} <a href="${createAccountURL}">${_("here")}</a>
                    % endif
                </div>
            </td>
        </tr>

        <tr>
            <td align="left"><img src="${ itemIcon }" alt="o" style="padding-right: 10px;"></td>
            <td align="left" width="100%">
                <div style="color: #444">
                    ${ _("Forgot your password?") } <span class="fakeLink" onclick="$E('forgotPasswordInfo').dom.style.display = ''; this.style.display = 'none';">${ ("Click here") }</span>
                </div>
            </td>
        </tr>
        <tr style="display: none;" id="forgotPasswordInfo">
            <td>&nbsp;</td>
            <td width="100%">
                <div style="padding: 5px 0;">
                    <div style="padding-bottom: 10px;">${ _("Please enter your e-mail address in the field below and your password will be sent to you") }</div>
                    <form action=${ forgotPasswordURL } method="POST">
                        <input type="text" name="email"> <input type="submit" class="btn" value="${ _("Send me my password") }">
                    </form>
                </div>
                <div style="padding: 5px 0; color: #444;">
                      <% from MaKaC.common.Configuration import Config    %>
                      % if "Local" not in Config.getInstance().getAuthenticatorList():
                           <em>${ _("If you <b>can't remember your password</b>, please click") } <a href="https://cernaccount.web.cern.ch/cernaccount/ResetPassword.aspx">${ ("here") }</a></em>
                      % else:
                           <em>${ _("<b>Note:</b> this works only with Indico local accounts, not with CERN NICE/External accounts; for these click") } <a href="https://cernaccount.web.cern.ch/cernaccount/ResetPassword.aspx">${ _("here") }</a></em>.
                      % endif
                </div>
            </td>
        </tr>
    </tbody></table>


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
