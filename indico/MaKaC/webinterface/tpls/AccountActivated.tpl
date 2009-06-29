
<center>
<b> <%= _("Your account is activated. You can now use your login to enter")%> <a href="%(loginURL)s"> <%= _("here")%></a></b><br><br>
<form action="%(mailLoginURL)s" method="POST">
 <%= _("If you can't remember your login and password, please use the button below to recieve them by email")%><br>
    <input type="submit" class="btn" value="<%= _("send me my login and password by email")%>">
</form>
</center>

