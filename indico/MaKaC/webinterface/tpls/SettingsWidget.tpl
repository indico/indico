<%page args="Languages=None"/>
<div id="settingsWidget" style="display:none" class="settingsWidget">
    <div style="line-height:17px">
        <span class="settingsWidgetHeader">${currentUser.getStraightFullName()}</span><br/>
        <span style="font-size:12px">${currentUser.getEmail()}</span>
    </div>
    <div class="settingsSeparator"></div>
    <div class="settingsWidgetSection">
        <form id="languageForm" method="post" action="${ urlHandlers.UHChangeLang.getURL() }">
            <span>${_("Language:")}</span>
            <select name="lang" onchange="$E('languageForm').dom.submit();">
            % for k,v in Languages:
                <option value="${ k }" ${"selected" if SelectedLanguage == k else ""}>${ v }</option>
            % endfor
            </select>
        </form>
    </div>
    % if currentUser:
        <div class="settingsWidgetSection"><a href="${ urlHandlers.UHUserDashboard.getURL(currentUser) }">${ _("My profile") }</a></div>
        <div class="settingsWidgetSection"><a href="${ urlHandlers.UHUserPreferences.getURL(currentUser) }">${ _("My preferences") }</a></div>
        % if currentUser.isAdmin():
            <div class="settingsWidgetSection"><a href="#" class="login-as">${ _("Login as...") }</a></div>
        % endif
        % if 'login_as_orig_user' in _session:
            <div class="settingsWidgetSection">
                <a href="#" class="undo-login-as">
                    ${ _("Switch back to") } ${ _session['login_as_orig_user']['user_name'] }
                </a>
            </div>
        % endif
        <div style="border-bottom: 1px solid #DDDDDD; margin-bottom:5px; margin-top:10px"></div>
        <div class="settingsWidgetSection"><a href="${ logoutURL }">${ _("Logout") }</a></div>
    % endif
</div>

<li id="userSettings">
    <a class="userSettings dropDownMenu fakeLink">${currentUser.getStraightAbrName()}</a>
</li>


<script type="text/javascript">

$("#settingsWidget a").click(function(){
    $(".userSettings").qtip('hide');
});

$(".userSettings").qtip({
    style: {
        minWidth: '200px',
        classes: 'qtip-rounded qtip-shadow qtip-popup',
        tip: {
            corner: true,
            width: 20,
            height: 15
        }
    },
    position: {
        my: 'top center',
        at: 'bottom center'
    },
    content: $('#settingsWidget'),
    show: {
        event: "click",
        effect: function() {
            $(this).fadeIn(300);
        }
    },
    hide: {
        event: 'unfocus click',
        fixed: true,
        effect: function() {
            $(this).fadeOut(300);
        }
    }
});
</script>
