<form action=%(quickAccessURL)s method="POST">
    <span class="titleCellFormat"> <%= _("Quick search: contribution ID")%></span> <input type="text" name="selContrib"><input type="submit" class="btn" value="<%= _("seek it")%>">
</form>
<br>
<form action=%(filterPostURL)s method="post">
    %(currentSorting)s
    <table width="100%%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td class="groupTitle"> <%= _("Filtering criteria")%></td>
        </tr>
        <tr>
            <td colspan="2">
                <table width="100%%">
                    <tr>
                        <td>
                            <table align="center" cellspacing="10" width="100%%">
                                <tr>
                                    <td class="titleCellFormat"> <%= _("Author search")%> <input type="text" name="authSearch" value=%(authSearch)s></td>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <table align="center" cellspacing="10" width="100%%">
                                <tr>
                                    <td align="center" class="titleCellFormat" style="border-bottom: 1px solid #5294CC; padding-right:10px"> <%= _("types")%></td>
                                    <td align="center" class="titleCellFormat" style="border-bottom: 1px solid #5294CC;"> <%= _("tracks")%></td>
                                    <td align="center" class="titleCellFormat" style="border-bottom: 1px solid #5294CC;"> <%= _("status")%></td>
                                    <td align="center" class="titleCellFormat" style="border-bottom: 1px solid #5294CC;"> <%= _("material")%></td>
                                </tr>
                                <tr>
                                    <td valign="top" style="border-right:1px solid #777777;">%(types)s</td>
                                    <td valign="top" style="border-right:1px solid #777777;">%(tracks)s</td>
                                    <td valign="top" style="border-right:1px solid #777777;">%(status)s</td>
                                    <td valign="top" style="border-right:1px solid #777777;">%(materials)s</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr>
                        <td align="center" style="border-top:1px solid #777777;padding:10px"><input type="submit" class="btn" name="OK" value="<%= _("apply")%>"></td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</form>
<br>
<table width="100%%" align="center" cellspacing="0" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td colspan="10" class="groupTitle">
                <table>
                    <tr>
                        <td nowrap class="groupTitle"> <%= _("Found contributions")%> (%(numContribs)s)</td>
                        <form action=%(addContribURL)s method="POST">
                        <td><input type="submit" class="btn" name="" value="<%= _("import contributions")%>"></td>
                        </form>
					    <form action=%(contributionsPDFURL)s method="post" target="_blank">
					    <td> %(contribsToPrint)s<input type="submit" class="btn" value="<%= _("PDF of all")%>"></td>
					    </form>
					    <form action=%(participantListURL)s method="post" target="_blank">
					    <td>%(contribsToPrint)s<input type="submit" class="btn" value="<%= _("author list")%>"></td>
					    </form>
                    </tr>
                </table>
            </td>
        </tr>
    <tr>
		<td></td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">%(numberImg)s<a href=%(numberSortingURL)s> <%= _("Id")%></a></td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">%(dateImg)s<a href=%(dateSortingURL)s> <%= _("Date")%></a></td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> <%= _("Duration")%></td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">%(typeImg)s<a href=%(typeSortingURL)s> <%= _("Type")%></a></td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">%(titleImg)s<a href=%(titleSortingURL)s> <%= _("Title")%></a></td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">%(speakerImg)s<a href=%(speakerSortingURL)s> <%= _("Presenter")%></a></td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">%(trackImg)s<a href=%(trackSortingURL)s> <%= _("Track")%></a></td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> <%= _("Status")%></td>
        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> <%= _("Material")%></td>
    </tr>
    <form action=%(contributionActionURL)s method="POST">
    <tr>
        %(contributions)s
    </tr>
	<tr><td>&nbsp;</td></tr>
	<tr><td colspan="11" align="center"><font color="black"> <%= _("Total Duration of Selected")%>: <b>%(totaldur)s</b></font></td></tr>
	<tr><td>&nbsp;</td></tr>

    <tr>
        <td colspan="10" style="border-top:2px solid #777777;padding-top:5px" valign="bottom" align="left">
            <table>
                <tr>
                    <td>
                        <input type="submit" class="btn" name="REMOVE" value="<%= _("remove selected")%>">
                    </td>
				</tr>
				<tr>
					<td colspan="10" valign="bottom" align="left">
						<input type="submit" class="btn" name="PDF" value="<%= _("PDF of selected")%>">
					</td>
				</tr>
				<tr>
					<td colspan="10" valign="bottom" align="left">
						<input type="submit" class="btn" name="AUTH" value="<%= _("author list of selected")%>">
					</td>
				</tr>
    </form>
            </table>
        </td>
    </tr>
</table>
