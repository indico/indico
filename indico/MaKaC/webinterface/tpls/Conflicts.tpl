<table width="90%"  align="center">
   <tr>
        <td class="groupTitle" align="center">
         ${ _("Conflicting Events")}
        </td>
   </tr>

   <tr>
    <td align="center" bgcolor="white" >
        <font color="#5294CC"> ${ _("Creating event")}: <b>${ name }, ${ start } - ${ end }</b>.</font>
    </td>
   </tr>



   ${ conflictlist }


    <form action="${ postURL }" method="post">

    <tr>
        <td align="center">
            <input type="submit" class="btn" onclick="history.go(-1);return false;" value="${ _("Back")}">
        </td>
    </tr>
    ${ conf }

    </form>
</table>
