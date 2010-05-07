<script type="text/javascript">
<!--

var newAbstract = false;

function selectAllTracks()
{
document.filterOptionForm.trackShowNoValue.checked=true
if (!document.filterOptionForm.track.length)
        {
            document.filterOptionForm.track.checked=true
        }else{
for (i = 0; i < document.filterOptionForm.track.length; i++)
    {
    document.filterOptionForm.track[i].checked=true
    }
}
}

function unselectAllTracks()
{
document.filterOptionForm.trackShowNoValue.checked=false
if (!document.filterOptionForm.track.length)
        {
            document.filterOptionForm.track.checked=false
        }else{
    for (i = 0; i < document.filterOptionForm.track.length; i++)
        {
        document.filterOptionForm.track[i].checked=false
        }
    }
}

function selectAllTypes()
{
document.filterOptionForm.typeShowNoValue.checked=true
if (!document.filterOptionForm.type.length)
        {
            document.filterOptionForm.type.checked=true
        }else{
for (i = 0; i < document.filterOptionForm.type.length; i++)
    {
    document.filterOptionForm.type[i].checked=true
    }
}
}

function unselectAllTypes()
{
document.filterOptionForm.typeShowNoValue.checked=false
if (!document.filterOptionForm.type.length)
        {
            document.filterOptionForm.type.checked=false
        }else{
for (i = 0; i < document.filterOptionForm.type.length; i++)
    {
    document.filterOptionForm.type[i].checked=false
    }
}
}

function selectAllStatus()
{
for (i = 0; i < document.filterOptionForm.status.length; i++)
    {
    document.filterOptionForm.status[i].checked=true
    }
}

function unselectAllStatus()
{
for (i = 0; i < document.filterOptionForm.status.length; i++)
    {
    document.filterOptionForm.status[i].checked=false
    }
}

function selectAllAccTracks()
{
document.filterOptionForm.accTrackShowNoValue.checked=true
if (!document.filterOptionForm.acc_track.length)
        {
            document.filterOptionForm.acc_track.checked=true
        }else{
for (i = 0; i < document.filterOptionForm.acc_track.length; i++)
    {
    document.filterOptionForm.acc_track[i].checked=true
    }
}
}

function unselectAllAccTracks()
{
document.filterOptionForm.accTrackShowNoValue.checked=false
if (!document.filterOptionForm.acc_track.length)
        {
            document.filterOptionForm.acc_track.checked=false
        }else{
for (i = 0; i < document.filterOptionForm.acc_track.length; i++)
    {
    document.filterOptionForm.acc_track[i].checked=false
    }
}
}

function selectAllAccTypes()
{
document.filterOptionForm.accTypeShowNoValue.checked=true
if (!document.filterOptionForm.acc_type.length)
        {
            document.filterOptionForm.acc_type.checked=true
        }else{
for (i = 0; i < document.filterOptionForm.acc_type.length; i++)
    {
    document.filterOptionForm.acc_type[i].checked=true
    }
}
}

function unselectAllAccTypes()
{
document.filterOptionForm.accTypeShowNoValue.checked=false
if (!document.filterOptionForm.acc_type.length)
        {
            document.filterOptionForm.acc_type.checked=false
        }else{
for (i = 0; i < document.filterOptionForm.acc_type.length; i++)
    {
    document.filterOptionForm.acc_type[i].checked=false
    }
}
}

function selectAllFields()
{

document.filterOptionForm.showID.checked=true
document.filterOptionForm.showPrimaryAuthor.checked=true
document.filterOptionForm.showTracks.checked=true
document.filterOptionForm.showType.checked=true
document.filterOptionForm.showStatus.checked=true
document.filterOptionForm.showAccTrack.checked=true
document.filterOptionForm.showAccType.checked=true
document.filterOptionForm.showSubmissionDate.checked=true
}

function unselectAllFields()
{
document.filterOptionForm.showID.checked=false
document.filterOptionForm.showPrimaryAuthor.checked=false
document.filterOptionForm.showTracks.checked=false
document.filterOptionForm.showType.checked=false
document.filterOptionForm.showStatus.checked=false
document.filterOptionForm.showAccTrack.checked=false
document.filterOptionForm.showAccType.checked=false
document.filterOptionForm.showSubmissionDate.checked=false
}
//-->
</script>

<table width="100%%" valign="top" align="left" cellspacing="0">
    <tr>
        <td class="titleCellFormat">
            <form action=%(accessAbstract)s method="post">
            <%= _("Quick search: Abstract ID")%> <input type="text" name="abstractId" size="4"><input type="submit" class="btn" value="<%= _("seek it")%>"><br>
            </form>
        </td>
    </tr>
</table>
<a href="" name="results"></a>
<table width="100%%" cellspacing="0" align="center" border="0">
    <tr>
       <td nowrap colspan="10">
            <div class="CRLgroupTitleNoBorder"><%= _("Displaying")%><strong> %(filteredNumberAbstracts)s </strong>
            <% if filteredNumberAbstracts == "1": %>
                <%= _("abstract")%>
            <% end %>
            <% else: %>
                <%= _("abstracts")%>
            <% end %>
            <% if filterUsed: %>
                (<%= _("Total")%>: <strong>%(totalNumberAbstracts)s</strong>)
            <% end %>
            </div>
            <form action=%(filterPostURL)s method="post" name="optionForm">
            <div class="CRLIndexList" >
                <% if filterUsed: %>
                    <input type="submit" class="btnRemove" name="resetFilters" value="Reset filters">
                    <span style="padding: 0px 6px 0px 6px">|</span>
                <% end %>
                <a id="index_filter" onclick="showFilters()" class="CAIndexUnselected" font-size="16" font-weight="bold" font-family="Verdana">
                  <% if filterUsed: %>
                    <%= _("Show filters")%>
                  <% end %>
                  <% else: %>
                    <%= _("Apply filters")%>
                  <% end %>
                </a>
            </div>
            </form>
        </td>
    </tr>
    <tr>
        <td colspan="10" align="left" width="100%%">
          <form action=%(filterPostURL)s method="post" name="filterOptionForm">
            <input type="hidden" name="operationType" value="filter" />
            %(filterMenu)s
            %(sortingOptions)s
          </form>
        </td>
    </tr>
    <tr>
        <td colspan="10" style="border-bottom:2px solid #777777;padding-top:5px" valign="bottom" align="left">
            <table>
                <form action=%(abstractSelectionAction)s method="post" name="abstractsForm" onSubmit="return atLeastOneSelected()">
                <tr>
                    <td valign="bottom" align="left" class="eventModifButtonBar"><input type="submit" class="btn" name="newAbstract" onclick="newAbstract = true;" value="<%= _("Add New")%>"></td>
                    <td valign="bottom" align="left"><input type="submit" class="btn" name="acceptMultiple" value="<%= _("accept") %>">
                    <td valign="bottom" align="left"><input type="submit" class="btn" name="rejectMultiple" value="<%= _("reject") %>">
                    <td valign="bottom" align="left"><input type="submit" class="btn" name="merge" value="<%= _("merge")%>"></td>
                    <td valign="bottom" align="left"><input type="submit" class="btn" name="auth" value="<%= _("author list")%>"></td>
                    <td valign="bottom" align="left">Export to:</td>
                    <td valign="bottom" align="left"><input type="image" name="excel" src=<%= excelIconURL%> border="0"></td>
                    <td valign="bottom" align="left"><input type="image" name="pdf" src=<%= pdfIconURL%> border="0"></td>
                    <td valign="bottom" align="left"><input type="image" name="xml" src=<%= xmlIconURL%> border="0"></td>
                </tr>
            </table>
        </td>
    </tr>
    <tr>
        %(abstractTitleBar)s
    </tr>
    <tr><td>
        <tbody id="abstractsItems">
        %(abstracts)s
        </tbody>
    </td></tr>
    <tr>
        <td colspan="10" style="border-top: 2px solid #777777; padding-top: 3px;" valign="bottom" align="left">
            <table>
                <tr>
                    <td valign="bottom" align="left" class="eventModifButtonBar"><input type="submit" class="btn" value="<%= _("new")%>"></td>
                    <td valign="bottom" align="left"><input type="submit" class="btn" name="acceptMultiple" value="<%= _("accept") %>">
                    <td valign="bottom" align="left"><input type="submit" class="btn" name="rejectMultiple" value="<%= _("reject") %>">
                    <td valign="bottom" align="left"><input type="submit" class="btn" name="merge" value="<%= _("merge")%>"></td>
                    <td valign="bottom" align="left"><input type="submit" class="btn" value="<%= _("author list")%>"></td>
                    <td valign="bottom" align="left">Export to:</td>
                    <td valign="bottom" align="left"><input type="image" name="excel" src=<%= excelIconURL%> border="0"></td>
                    <td valign="bottom" align="left"><input type="image" name="pdf" src=<%= pdfIconURL%> border="0"></td>
                    <td valign="bottom" align="left"><input type="image" name="xml" src=<%= xmlIconURL%> border="0"></td>
            </tr>
            </form>
            </table>
        </td>
    </tr>
</table>

<script type="text/javascript">
    function onMouseOver(element) {
        if ($E(element).dom.style.backgroundColor ==='transparent') {
           $E(element).dom.style.backgroundColor='rgb(255, 246, 223)';
        }
    }

    function onMouseOut(element) {
        var inputNodes = IndicoUtil.findFormFields($E(element))
        for (i = 0; i < inputNodes.length; i++) {
            var node = inputNodes[i];
            if (node.type == "checkbox") {
                if(node.checked !== true) {
                    $E(node.name+node.value).dom.style.backgroundColor='transparent';
                } else {
                    $E(node.name+node.value).dom.style.backgroundColor = "#CDEB8B";
                }
            }
        }
    }


    function atLeastOneSelected() {
        if(!newAbstract) {
            var inputNodes = IndicoUtil.findFormFields($E("abstractsItems"))
            for (i = 0; i < inputNodes.length; i++)
            {
                var node = inputNodes[i];
                if (node.type == "checkbox") {
                    if(node.checked == true) {
                        return true;
                    }
                }
            }

            var dialog = new WarningPopup($T("Warning"), $T("No abstract selected! Please select at least one."));
            dialog.open();

            return false;
        } else {
            return true;
        }
    }

    function isSelected(element) {
        var inputNodes = IndicoUtil.findFormFields($E(element))
        for (i = 0; i < inputNodes.length; i++) {
            var node = inputNodes[i];
            if (node.type == "checkbox") {
                if(node.checked == true) {
                    $E(node.name+node.value).dom.style.backgroundColor = "#CDEB8B";
                } else {
                    $E(node.name+node.value).dom.style.backgroundColor='transparent';
                }
            }
        }
    }

    function selectAll()
    {
        if (!document.abstractsForm.abstracts.length)
        {
            document.abstractsForm.abstracts.checked=true
        }else{
            for (i = 0; i < document.abstractsForm.abstracts.length; i++)
            {
                document.abstractsForm.abstracts[i].checked=true;
            }
        }
        isSelected("abstractsItems")
    }

    function deselectAll()
    {
        if (!document.abstractsForm.abstracts.length)
        {
            document.abstractsForm.abstracts.checked=false
        }else{
            for (i = 0; i < document.abstractsForm.abstracts.length; i++)
            {
                document.abstractsForm.abstracts[i].checked=false;
            }
        }
        isSelected("abstractsItems")
    }

    function showFilters() {
        if ($E("filterMenu").dom.style.display == "") {
<% if filterUsed: %>
            $E("index_filter").set('<%= _("Show filters")%>');
<% end %>
<% else: %>
            $E("index_filter").set('<%= _("Apply filters")%>');
<% end %>
            $E('index_filter').dom.className = "CRLIndexUnselected";
            $E("filterMenu").dom.style.display = "none";
        }else {
            $E("index_filter").set('<%= _("Hide filters")%>');
            $E('index_filter').dom.className = "CRLIndexSelected";
            $E("filterMenu").dom.style.display = "";
        }
    }
</script>
