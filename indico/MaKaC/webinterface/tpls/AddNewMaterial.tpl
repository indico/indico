
<table width="100%%" class="filesTab"><tr><td>
<form action=%(postURL)s method="POST" enctype="multipart/form-data" name="submitfile">
<input type="hidden" name="numFieldChange" id="numFieldChange" value=""/>
<table style="border-left: 1px solid #777777">
    <tr>
        <td colspan="5" class="groupTitle"><%= _("Add new material")%></td>
    </tr>
    %(errors)s
    <tr>
        <td class="titleCellTD">
            <span class="titleCellFormat"><%= _("Number of files:")%>
            </span>
            <select name="nbFiles" onchange="$E('numFieldChange').set('true');this.form.submit();">
                %(selectNumberOfFiles)s
            </select>
        </td>
        <td>
            %(fileSubmitForms)s
        </td>
    </tr>
    <tr>
        <td class="titleCellTD">
            <span class="titleCellFormat"><%= _("Number of urls:")%>
            </span>
            <select name="nbLinks" onchange="$E('numFieldChange').set('true');this.form.submit();">
                %(selectNumberOfLinks)s
            </select>
        </td>
        <td>
            %(linkSubmitForms)s
        </td>
    </tr>
    %(conversion)s
    <tr>
        <td colspan="2">&nbsp;</td>
    </tr>
    <tr>
        <td>
            <input type="submit" class="btn" name="OK" value="submit">
            %(CancelButton)s
        </td>
    </tr>
</table>
</form>
<br>
</td></tr></table>
