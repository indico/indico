<table width="90%%" bgcolor="#808080" align="center">
    <tr>
        <td bgcolor="#000060" align="center">
            <b><font size="+2" color="white"> <%= _("Creation of a new event")%></font></b>
        </td>
    </tr>
    <tr>
        <td bgcolor="#E8F8FF">
            <font size="-1"> <%= _("This tool offers you the possibility of selecting a special type for the event you want to register. By selecting a type you'll have a more customised interface adapted to that type (with some hidden options which are not useful in some types, for example).<br> If you are not sure, don't worry, you can always change from one type to another.")%></font>
        </td>
    </tr>
    <tr>
        <td bgcolor="white">
             <%= _("Select the type of event you want to create")%>:<br><br>
            <form action="%(postURL)s" method="POST">
                <table width="90%%" align="center">
                    %(eventTypes)s
                    <tr>
                        <td valign="top"><input type="submit" class="btn" name="event_type" value="<%= _("default")%>"></td>
                        <td align="left" width="100%%"><font size="-1"> <%= _("No type is specified, the event will be shown using the default interface")%></font></td>
                        </td>
                    </tr>
                </table>
            </form>
        </td>
    </tr>
</table>
