
<center>
    <form action="${ createPDFURL }" method="post">
    ${ contribIdsList }
    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle"> ${ _("Contribution to PDF")}</td>
        </tr>
        <tr>
            <td>
                <table width="100%">
                    <tr>
                        <td>
                            ${ _("PDF type :")}<br>
                            <input type="radio" name="displaytype" value="ContributionList" checked="checked"> ${ _("Contribution list (more details)")}<br>
                            <input type="radio" name="displaytype" value="bookOfAbstract"> ${ _("Book of abstract (less details)")}<br>
                            <input type="radio" name="displaytype" value="bookOfAbstractBoardNo"> ${ _("Book of abstract (sorted by board# - useful for posters)")}<br>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr>
            <td>
                &nbsp;
            </td>
        </tr>
        <tr>
            <td>
                <input type="submit" class="btn" value="${ _("get pdf")}" name="ok">
            </td>
        </tr>
    </table>
<br>
</form>
</center>
