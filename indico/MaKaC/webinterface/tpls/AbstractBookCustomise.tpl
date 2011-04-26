<form action=${ getPDFURL } method="post" target="_blank" style="margin: 0;">

    <div class="groupTitle">${ _("Book of Abstracts")}</div>


<table class="conferenceDetails">
    <tbody>
    <tr>
        <td align="right" valign="top" class="displayField"><b>${ _("Sort by")}:</b></td>
        <td><input type="radio" name="sortBy" value="number" checked="checked">${ _("ID")}<br>
                            <input type="radio" name="sortBy" value="name">${ _("Title")}<br>
                            <input type="radio" name="sortBy" value="sessionTitle">${ _("Session title")}<br>
                            <input type="radio" name="sortBy" value="speaker">${ _("Presenter")}<br>
                            <input type="radio" name="sortBy" value="schedule">${ _("Schedule")} <small>(${ _("this BoA will print out just scheduled abstracts")})</small><br></td>
    </tr>
    <tr>
        <td>&nbsp;</td>
        <td><input type="submit" style="margin-top: 20px;" class="btn" value="${ _("get pdf")}" name="ok" /></td>
    </tr>
    </tbody>
</table>



</form>
