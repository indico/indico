
<div class="container" style="width: 100%%; margin: 50px auto; max-width: 800px">

<div class="groupTitle" style="margin-bottom: 30px; font-size: 25pt;    "><%= _("Log in to Indico")%></div>

<form name="signInForm" action=%(postURL)s method="POST">
<input type="hidden" name="returnURL" value=%(returnURL)s>

<table class="groupTable">
    <tr>

        <script type="text/javascript">
        //Free JavaScripts on http://www.ScriptBreaker.com
        var cookiesEnabled = false;
        
         
        // Check whether cookies enabled
        document.cookie = "Enabled=true";
        var cookieValid = document.cookie;
           
        // if retrieving the VALUE we just set actually works
        // then we know cookies enabled
        if (cookieValid.indexOf("Enabled=true") != -1)
        {
           cookiesEnabled = true;
        }
        else
        {
           cookiesEnabled = false;
        }
         
        if(cookiesEnabled == false) document.write('<td colspan="2"><br><center><font size=+1 color=red>Please enable cookies in your browser!</font></center><br></td></tr><tr>');
        </SCRIPT>
        <td class="titleCellTD">
            <span class="titleCellFormat"><%= _("User Name")%></span>
        </td>
        <td class="contentCellTD" id="usernameInput">                                    
            <input type="text" name="login" size="40" value=%(login)s>
        </td>
    </tr>
    <tr>
        <td class="titleCellTD">
            <span class="titleCellFormat"><%= _("Password")%></span>
        </td>
        <td class="contentCellTD" id="passwordInput">
            <input type="password" name="password" size="40">
        </td>
    </tr>
    
    <% if NiceMsg: %>
    <tr>
        <td class="titleCellTD">&nbsp;</td>
        <td class="contentCellTD">
            <em>%(NiceMsg)s</em>
        </td>
    </tr>
    <% end %>
    
    <% if msg: %>
        <tr>
            <td class="titleCellTD">&nbsp;</td>
            <td class="contentCellTD">
                <span style="color: darkred">%(msg)s</span>
            </td>
        </tr>
    <% end %>
    
    <tr>
        <td class="titleCellTD">&nbsp;</td>
        <td class="contentCellTD">
            <div class="yellowButton loginButton">
                <input type="submit" id="loginButton" value="<%= _("Login")%>" name="signIn">
            </div>
        </td>
    </tr>
</table>
</form>

<script type="text/javascript">
    document.signInForm.login.focus();
</script>

<div style="margin: 20px 30px 0 30px;">

    <table width="100%%" cellspacing="5" cellpadding="0"><tbody>
        <tr>
            <td align="left"><img src="%(itemIcon)s" alt="o" style="padding-right: 10px;"></td>
            <td align="left" width="100%%">
                <div style="padding: 5px 0; color: #444">
                    %(createAccount)s
                </div>
            </td>
        </tr>
        
        <tr>
            <td align="left"><img src="%(itemIcon)s" alt="o" style="padding-right: 10px;"></td>
            <td align="left" width="100%%">
                <div style="color: #444">
                    <%= ("Forgot your password?") %> <span class="fakeLink" onclick="$E('forgotPasswordInfo').dom.style.display = ''; this.style.display = 'none';"><%= ("Click here") %></span>
                </div>
            </td>
        </tr>
        <tr style="display: none;" id="forgotPasswordInfo">
            <td>&nbsp;</td>
            <td width="100%%">
                <div style="padding: 5px 0;">
                    <div style="padding-bottom: 10px;"><%= _("Please enter your e-mail address in the field below and your password will be sent to you") %></div>
                    <form action=%(forgotPasswordURL)s method="POST">
                        <input type="text" name="email"> <input type="submit" class="btn" value="<%= _("Send me my password") %>">
                    </form>
                </div>
                <div style="padding: 5px 0; color: #444;">
                      <% from MaKaC.common.Configuration import Config    %>
                      <% if "Local" not in Config.getInstance().getAuthenticatorList(): %>
                           <em><%= ("If you <b>can't remember your password</b>, please click") %> <a href="https://cernaccount.web.cern.ch/cernaccount/ResetPassword.aspx"><%= ("here") %></a></em>
                      <% end %>
                      <% else: %>
                           <em><%= _("<b>Note:</b> this works only with Indico local accounts, not with CERN NICE/External accounts; for these click") %> <a href="https://cernaccount.web.cern.ch/cernaccount/ResetPassword.aspx"><%= _("here") %></a></em>.
                      <% end %>
                </div>
            </td>
        </tr>
    </tbody></table>
    

</div>

</div>