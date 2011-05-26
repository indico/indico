% if currentUser:
        <li><span>${ _("Logged in as")}</span><a href="${ urlHandlers.UHUserDetails.getURL(currentUser) }">${ currentUser.getAbrName() }</a></li>
        % if currentUser.isAdmin():
            <li><a href="#" onclick="loginAsManager.drawUsersPopup();">${ _("Login as...") }</a></li>
        % endif
        <li style="border-right: none;"><a href="${ logoutURL }">${ _("Logout") }</a></li>
% else:
     <li class="loginHighlighted" style="border-right: none;"><a href="${ loginURL }"><strong style="color: white">${ _("Login")}</strong></a></li>
% endif

<script>
% if currentUser:
    % if currentUser.isAdmin():
        var loginAsManager = new LoginAsManager();
    % endif
% endif
</script>
