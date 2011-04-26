<table width="95%" align="center" valign="top" cellspacing="0">
    <tr>
        <td>
            <table width="100%" style="padding-left:1px solid #777777">
                <tr>
                    <td>
                        <table bgcolor="white" width="100%">
                            <tr>
                                <form action=${ accessAbstract } method="post">
                                <td class="titleCellFormat"> ${ _("Display abstract with ID")} = <input type="text" name="abstractId" size="4"><input type="submit" class="btn" value="${ _("go")}"><br>
                                </td>
                                </form>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    <tr>
        <td>
            <br>
            <form action=${ filterPostURL } method="POST">
                ${ currentSorting }
                <table width="100%" border="0" style="border-left: 1px solid #777777">
                    <tr>
                        <td class="groupTitle"> ${ _("Display options")}</td>
                    </tr>
                    <tr>
                        <td>
                            <table width="100%">
                                <tr>
                                    <td>
                                        <table align="center" cellspacing="10" width="100%">
                                            <tr>
                                                <td align="center" class="titleCellFormat" style="border-bottom: 1px solid #5294CC; padding-right:10px"> ${ _("show contribution types")}</td>
                                                <td align="center" class="titleCellFormat" style="border-bottom: 1px solid #5294CC;"> ${ _("show in status")}</td>
                                                <td align="center" class="titleCellFormat" style="border-bottom: 1px solid #5294CC;"> ${ _("show acc. contribution types")}</td>
                                                <td align="center" class="titleCellFormat" style="border-bottom: 1px solid #5294CC;"> ${ _("others")}</td>
                                            </tr>
                                            <tr>
                                                <td valign="top" style="border-right:1px solid #777777;">${ types }</td>
                                                <td valign="top" style="border-right:1px solid #777777;">${ status }</td>
                                                <td valign="top" style="border-right:1px solid #777777;">${ accTypes }</td>
                                                <td valign="top">${ others }</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                                <tr>
                                    <td align="center" style="border-top:1px solid #777777;padding:10px"><input type="submit" class="btn" name="OK" value="${ _("apply")}"></td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </form>
        </td>
    </tr>
    <tr>
        <td>
            <br>
            <a name="abstracts"></a>
            <table width="100%" cellspacing="0" border="0" style="border-left: 1px solid #777777;padding-left:2px">
                <tr>
                    <td colspan="6" class="groupTitle">
                        <table>
                            <tr>
                                <td class="groupTitle"> ${ _("Submitted abstracts")} (${ number })</td>
                                <form action=${ abstractsPDFURL } method="post" target="_blank">
                                <td>${ abstractsToPrint }<input type="submit" class="btn" value="${ _("PDF of all")}"></td>
                                </form>
                                <form action=${ participantListURL } method="post" target="_blank">
                                <td>${ abstractsToPrint }<input type="submit" class="btn" value="${ _("Participant list of all")}"></td>
                                </form>
                                <form action=${ allAbstractsURL } target="_blank" method="POST">
                                <td><input type="submit" class="btn" name="all" value="${ _("Go to all abstracts")}"></td>
                                </form>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"><a href=${ numberSortingURL }> ${ _("ID")}</a> ${ numberImg }</td>
                    <td class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> ${ _("Title")}</td>
                    <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #5294CC;border-right:5px solid #FFFFFF"><a href=${ typeSortingURL }> ${ _("Type")}</a> ${ typeImg }</td>
                    <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #5294CC;border-right:5px solid #FFFFFF"><a href=${ statusSortingURL }> ${ _("Status")}</a> ${ statusImg }</td>
                    <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #5294CC;border-right:5px solid #FFFFFF"> ${ _("Acc. Type")}</td>
                    <td class="titleCellFormat" style="border-bottom: 1px solid #5294CC;"><a href=${ dateSortingURL }> ${ _("Submission date")}</a> ${ dateImg }</td>
                </tr>
                <tr><td>&nbsp;</td></tr>
                <form action=${ actionURL } method="post" target="_blank">
                ${ abstracts }
                <tr>
                    <td colspan="3" style="border-top:1px solid #777777;" valign="bottom" align="left">
                        <table align="left">
                            <tr>
                                <td valign="bottom" align="left">
                                    <input type="submit" class="btn" name="PDF" value="${ _("PDF of selected")}" style="width:264px">
                                </td>
                            </tr>
                            <tr>
                                <td valign="bottom" align="left">
                                    <input type="submit" class="btn" name="PART" value="${ _("participant list of selected")}" style="width:264px">
                                </td>
                                </form>
                            </tr>
                        </table>
                    </td>
                    <td colspan="3" bgcolor="white" align="center" style="border-top:1px solid #777777;border-left:1px solid #777777;color:black">
                        <b> ${ _("Total")} : ${ number }&nbsp;${ _("abstract(s)")}</b>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
