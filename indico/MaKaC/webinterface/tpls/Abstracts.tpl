
<table width="95%%" valign="top" align="center" cellspacing="0">
	<tr>
		<td>
			<table width="100%%" align="center" style="padding-left:1px solid #777777">
				<tr>
					<td>
						<table bgcolor="white" width="100%%">
							<tr>
								<form action=%(accessAbstract)s method="post">
								<td class="titleCellFormat"> <%= _("Quick search: Abstract ID")%> <input type="text" name="abstractId" size="4"><input type="submit" class="btn" value="<%= _("seek it")%>"><br>
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
<script type="text/javascript">
<!--
function selecAllTracks()
{
document.optionForm.trackShowNoValue.checked=true
if (!document.optionForm.selTracks.length)
        {
            document.optionForm.selTracks.checked=true
        }else{
for (i = 0; i < document.optionForm.selTracks.length; i++)
	{
	document.optionForm.selTracks[i].checked=true
	}
}
}

function unselecAllTracks()
{
document.optionForm.trackShowNoValue.checked=false
if (!document.optionForm.selTracks.length)
        {
            document.optionForm.selTracks.checked=false
        }else{
    for (i = 0; i < document.optionForm.selTracks.length; i++)
        {
        document.optionForm.selTracks[i].checked=false
        }
    }
}

function selecAllTypes()
{
document.optionForm.typeShowNoValue.checked=true
if (!document.optionForm.selTypes.length)
        {
            document.optionForm.selTypes.checked=true
        }else{
for (i = 0; i < document.optionForm.selTypes.length; i++)
	{
	document.optionForm.selTypes[i].checked=true
	}
}
}

function unselecAllTypes()
{
document.optionForm.typeShowNoValue.checked=false
if (!document.optionForm.selTypes.length)
        {
            document.optionForm.selTypes.checked=false
        }else{
for (i = 0; i < document.optionForm.selTypes.length; i++)
	{
	document.optionForm.selTypes[i].checked=false
	}
}
}

function selecAllStatus()
{
for (i = 0; i < document.optionForm.selStatus.length; i++)
	{
	document.optionForm.selStatus[i].checked=true
	}
}

function unselecAllStatus()
{
for (i = 0; i < document.optionForm.selStatus.length; i++)
	{
	document.optionForm.selStatus[i].checked=false
	}
}

function selecAllAccTracks()
{
document.optionForm.accTrackShowNoValue.checked=true
if (!document.optionForm.selAccTracks.length)
        {
            document.optionForm.selAccTracks.checked=true
        }else{
for (i = 0; i < document.optionForm.selAccTracks.length; i++)
	{
	document.optionForm.selAccTracks[i].checked=true
	}
}
}

function unselecAllAccTracks()
{
document.optionForm.accTrackShowNoValue.checked=false
if (!document.optionForm.selAccTracks.length)
        {
            document.optionForm.selAccTracks.checked=false
        }else{
for (i = 0; i < document.optionForm.selAccTracks.length; i++)
	{
	document.optionForm.selAccTracks[i].checked=false
	}
}
}

function selecAllAccTypes()
{
document.optionForm.accTypeShowNoValue.checked=true
if (!document.optionForm.selAccTypes.length)
        {
            document.optionForm.selAccTypes.checked=true
        }else{
for (i = 0; i < document.optionForm.selAccTypes.length; i++)
	{
	document.optionForm.selAccTypes[i].checked=true
	}
}
}

function unselecAllAccTypes()
{
document.optionForm.accTypeShowNoValue.checked=false
if (!document.optionForm.selAccTypes.length)
        {
            document.optionForm.selAccTypes.checked=false
        }else{
for (i = 0; i < document.optionForm.selAccTypes.length; i++)
	{
	document.optionForm.selAccTypes[i].checked=false
	}
}
}

function selecAllFields()
{

document.optionForm.showID.checked=true
document.optionForm.showPrimaryAuthor.checked=true
document.optionForm.showTracks.checked=true
document.optionForm.showType.checked=true
document.optionForm.showStatus.checked=true
document.optionForm.showAccTrack.checked=true
document.optionForm.showAccType.checked=true
document.optionForm.showSubmissionDate.checked=true
}

function unselecAllFields()
{
document.optionForm.showID.checked=false
document.optionForm.showPrimaryAuthor.checked=false
document.optionForm.showTracks.checked=false
document.optionForm.showType.checked=false
document.optionForm.showStatus.checked=false
document.optionForm.showAccTrack.checked=false
document.optionForm.showAccType.checked=false
document.optionForm.showSubmissionDate.checked=false
}
//-->
</script>

			<form action=%(filterPostURL)s name="optionForm" method="post">
				%(currentSorting)s
				%(menu)s
			</form>
		</td>
	</tr>
	<tr>
		<td>
			<br>
				<a name="abstracts"></a>
				<table width="100%%" cellspacing="0" align="center" border="0" style="border-left: 1px solid #777777;padding-left:2px">
					<tr>
						<td colspan="9">
							%(generateExcel)s
						</td>
					</tr>
					<tr>
						<td colspan="9" class="groupTitle">
                            <table>
                                <tr>
                                    <td nowrap class="groupTitle"> <%= _("Found Abstracts")%> (%(number)s)</td>
                                    <form action=%(newAbstractURL)s method="POST">
                                    <td class="titleCellFormat"><input type="submit" class="btn" value="<%= _("new")%>"></td>
                                    </form>
                                    <form action=%(abstractsPDFURL)s method="post" target="_blank">
                                    <td>%(abstractsToPrint)s<input type="submit" class="btn" value="<%= _("PDF of all")%>"></td>
                                    </form>
                                    <form action=%(abstractsXMLURL)s method="post" target="_blank">
                                    <td>%(abstractsToPrint)s<input type="submit" class="btn" value="<%= _("XML of all")%>"></td>
                                    </form>
                                    <form action=%(participantListURL)s method="post" target="_blank">
                                    <td>%(abstractsToPrint)s<input type="submit" class="btn" value="<%= _("author list of all")%>"></td>
                                    </form>
                            </tr>
                            </table>
                        </td>
					</tr>
					<tr>
						%(abstractTitleBar)s
					</tr>
                    <form action=%(abstractSelectionAction)s method="post">
					%(abstracts)s
					%(fieldsToPrint)s
					<tr>
						<td colspan="4" style="border-top:1px solid #777777;" valign="bottom" align="left">
						<table align="left" border="0">
                            <tr>
                                <td colspan="4">
                                    <table>
                                        <tr>
                                            <td>
                                                <input type="submit" class="btn" name="merge" value="<%= _("merge selected abstracts")%>" style="width:264px">
                                            </td>
                                        </tr>
                                        <tr>
                                            <td>
                                                <input type="submit" class="btn" name="PDF" value="<%= _("get PDF of selected abstracts")%>" style="width:264px">
                                            </td>
                                        </tr>
                                        <tr>
                                            <td>
                                                <input type="submit" class="btn" name="AUTH" value="<%= _("get author list of selected abstracts")%>" style="width:264px">
                                            </td>
                                            <td>
                                                <input type="submit" class="btn" name="acceptMultiple" value="Accept multiple">
                                            </td>
                                            <td>
                                                <input type="submit" class="btn" name="rejectMultiple" value="Reject multiple">
                                            </td>
                            </form>
                                        </tr>
                                    </table>
                                </td>
                            </tr>
						</table>
					</td>
					<td colspan="5" bgcolor="white" align="center" style="border-top:1px solid #777777;border-left:1px solid #777777;color:black">
						<b> <%= _("Total")%> : %(number)s  <%= _("abstract(s)")%></b>
					</td>
				</tr>
			</table>
		</td>
	</tr>
</table>
