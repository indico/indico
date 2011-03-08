<table align="center" style="border-top:1px solid #777777;
                                border-left:1px solid #777777;
                                background:#D9D9D9;"
                                width="90%">
    <tr>
        <td align="left" width="33%">${ dateInterval }</td>
        <td align="center" width="33%">${ place }</td>
        <td align="right" width="33%">${ name }</td>
    </tr>
    <tr style="background:white">
        <form action=${ remEntriesURL } method="POST">
        <td colspan="3">
            <table width="90%" align="center">
                ${ entries }
            </table>
        </td>
    </tr>
    <tr>
        <td align="left" colspan="3">
            <table>
                <tr>
                    <td>
                        <table>
                            <tr>
                                <td>
                                    <input type="submit" class="btn" value="${ _("remove selected")}">
                                </td>
                                </form>
                                <form action=${ addContribURL } method="POST">
                                <td>
                                    <input type="submit" class="btn" value="${ _("add contribution")}">
                                </td>
                                </form>
                                <form action=${ addBreakURL } method="POST">
                                <td>
                                    <input type="submit" class="btn" value="${ _("add break")}">
                                </td>
                                </form>
                                <form action=${ compactURL } method="POST">
                                <td>
                                    <input type="submit" class="btn" value="${ _("compact")}">
                                </td>
                                </form>
                            </tr>
                        </table>
                    </td>
                    <td align="right" width="100%">
                        <table>
                            <tr>
                                <form action=${ delSlotURL } method="POST">
                                <td>
                                    <input type="submit" class="btn" value="${ _("delete this slot")}">
                                </td>
                                </form>
                                <form action=${ editSlotURL } method="POST">
                                <td>
                                    <input type="submit" class="btn" value="${ _("modify this slot")}">
                                </td>
                                </form>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>