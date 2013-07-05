
<center>
<b> ${ _("Your account is activated. You can now use your login to enter")} <a href="${ loginURL }"> ${ _("here")}</a></b><br><br>
<form action="${ mailLoginURL }" method="POST">
    ${ _("If you can't remember your login and password, please use the button below to receive a link to reset your password by email")}
    <br>
    <input type="submit" class="btn" value="${ _("Reset my password")}">
</form>
</center>
