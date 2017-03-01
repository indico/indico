<table align="center" width="75%">
    <tr>
       <td class="formTitle"> ${ _("List of participants")}</td>
    </tr>
    <tr>
        <td>
            <br>
                <table width="100%" align="center" border="0" style="border-left: 1px solid #777777">
                    <tr>
                        <td colspan="2" class="groupTitle" width="100%"> ${ _("Submitters")}</td>
                    </tr>
                    <tr>
                        <td width="100%">
                            <table width="100%">
                            ${ submitters }
                            </table>
                        </td>
                        <td align="right" valign="top">
                            <form action="mailto:${ submitterEmails }" method="POST" enctype="text/plain">
                                <input type="submit" class="btn" value="${ _("send")}">
                            </form>
                            ${ showSubmitters }
                        </td>
                    </tr>
                </table>
        </td>
    </tr>
    <tr>
        <td>
            <br>
                <table width="100%" align="center" border="0" style="border-left: 1px solid #777777">
                    <tr>
                        <td colspan="2" class="groupTitle" width="100%"> ${ _("Primary authors")}</td>
                    </tr>
                    <tr>
                        <td width="100%">
                            <table width="100%">
                            ${ primaryAuthors }
                            </table>
                        </td>
                        <td align="right" valign="top">
                            <form action="mailto:${ primaryAuthorEmails }" method="POST" enctype="text/plain">
                                <input type="submit" class="btn" value="${ _("send")}">
                            </form>
                            ${ showPrimaryAuthors }
                        </td>
                    </tr>
                </table>
        </td>
    </tr>
    <tr>
        <td>
            <br>
                <table width="100%" align="center" border="0" style="border-left: 1px solid #777777">
                    <tr>
                        <td colspan="2" class="groupTitle" width="100%"> ${ _("Co-Authors")}</td>
                    </tr>
                    <tr>
                        <td width="100%">
                            <table width="100%">
                            ${ coAuthors }
                            </table>
                        </td>
                        <td align="right" valign="top">
                            <form action="mailto:${ coAuthorEmails }" method="POST" enctype="text/plain">
                                <input type="submit" class="btn" value="${ _("send")}">
                            </form>
                            ${ showCoAuthors }
                        </td>
                    </tr>
                </table>
        </td>
    </tr>
</table>
