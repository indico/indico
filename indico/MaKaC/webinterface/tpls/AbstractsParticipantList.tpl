
<table align="center" width="100%">
    <tr>
       <td class="groupTitle"> ${ _("List of participants")}</td>
    </tr>
    <tr>
        <td>
            <br>
                <table width="100%" align="center" border="0">
                    <tr>
                        <td colspan="2" class="groupSubTitle" width="100%"> ${ _("Submitters")}</td>
                    </tr>
                    <tr>
                        <td width="100%">
                            <table width="100%">
                            ${ submitters }
                            </table>
                        </td>
                        <td align="right" valign="top">
                            <form action="mailto:${ submitterEmails }" method="POST" enctype="text/plain">
                                <input type="submit" class="btn" value="${ _("compose email")}">
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
                <table width="100%" align="center" border="0">
                    <tr>
                        <td colspan="2" class="groupSubTitle" width="100%"> ${ _("Primary authors")}</td>
                    </tr>
                    <tr>
                        <td width="100%">
                            <table width="100%">
                            ${ primaryAuthors }
                            </table>
                        </td>
                        <td align="right" valign="top">
                            <form action="mailto:${ primaryAuthorEmails }" method="POST" enctype="text/plain">
                                <input type="submit" class="btn" value="${ _("compose email")}">
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
                <table width="100%" align="center" border="0">
                    <tr>
                        <td colspan="2" class="groupSubTitle" width="100%"> ${ _("Co-Authors")}</td>
                    </tr>
                    <tr>
                        <td width="100%">
                            <table width="100%">
                            ${ coAuthors }
                            </table>
                        </td>
                        <td align="right" valign="top">
                            <form action="mailto:${ coAuthorEmails }" method="POST" enctype="text/plain">
                                <input type="submit" class="btn" value="${ _("compose email")}">
                            </form>
                            ${ showCoAuthors }
                        </td>
                    </tr>
                </table>
        </td>
    </tr>
</table>
