<center>
<b>${ _("Your account is not activated.")}</b><br><br>
% if not moderated:
<form action="${ mailActivationURL }" method="POST">
 ${ _("If you haven't received the email with the activation link, click on the following button to receive it")}<br>
    <input type="submit" class="btn" value="${ _("send me the activation email")}">
</form>
% endif
</center>
