<br>
<form action=%(postURL)s method="POST">
<input type="hidden" name="materialType" value=%(matType)s>
<input type="hidden" name="description" value=%(description)s>
<input type="hidden" name="fileName" value=%(fileName)s>
<input type="hidden" name="filePath" value=%(filePath)s>

<table width="90%%" align="center" border="0" style="border-left: 1px solid #777777">
    <tr>
        <td colspan="5" class="groupTitle"><%= _("Submitting material for a contribution")%></td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD">
            <span class="titleCellFormat"><%= _("Contribution")%></span>
        </td>
        <td bgcolor="white" width="80%%">%(contribId)s-%(contribTitle)s</td>
    </tr>
    <tr>
        <td colspan="2" align="center" width="100%%">
            <table align="center">
                <tr>
                    <td style="color:red" align="center"><%= _("WARNING!!")%></td>
                </tr>
                <tr>
                    <td style="border-top:1px solid red;
                                border-left:1px solid red;
                                border-right:1px solid red;
                                border-bottom:1px solid red">
                        <%= _("You have selected to submit as %(matTypeCaption)s material the file")%>:
                        <ul>
                            <li><i>%(selFileName)s</i> (%(selFileSize)s)</li>
                        </ul>
                        <%= _("but there is ALREADY SOME EXISTING MATERIAL of this type")%>:
                        <ul>
                            <li><i>%(oldFileName)s</i> (%(oldFileSize)s)</li>
                        </ul>
                        <%= _("if you continue the EXISTING FILES WILL BE REPLACED")%>.
                        <br>
                        <br>
                        <%= _("How do you want to proceed")%>?
                        <br>
                        <br>
                        <table align="center">
                            <tr>
                                <td><input type="submit" class="btn" name="UPDATE" value="<%= _("replace existing material")%>"></td>
                                <td><input type="submit" class="btn" name="CANCEL" value="<%= _("cancel")%>"></td>
                            </tr>
                        </table>
                        <br>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
</form>
<br>
