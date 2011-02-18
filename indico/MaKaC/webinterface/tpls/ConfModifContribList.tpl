<%!
location = self._conf.getLocation()
room = self._conf.getRoom()

if location:
    locationName = location.getName()
    address = self._conf.getLocation().getAddress().replace('\r\n','\\n').replace('\n','\\n')
else:
    locationName = 'None'
    address = ''

if room:
    roomName = room.name
else:
    roomName = 'None'

%>

<form action=<%= quickSearchURL %> method="POST">
    <span class="titleCellFormat"> <%= _("Quick search: contribution ID")%></span> <input type="text" name="selContrib"><input type="submit" class="btn" value="<%= _("seek it")%>">
</form>
<br>

<script type="text/javascript">
<!--
    function selectStatuses()
    {
        for (i = 0; i < document.filterOptionForm.statuses.length; i++)
        {
            document.filterOptionForm.statuses[i].checked=true;
        }
    }

    function selectOneStatus(elementName)
    {
        var inputNodes = IndicoUtil.findFormFields($E(elementName))
        for (i = 0; i < inputNodes.length; i++)
        {
            var node = inputNodes[i];
            if (node.type == "checkbox") {
                node.checked = true;
            }
        }
    }

    function unselectOneStatus(elementName)
    {
        var inputNodes = IndicoUtil.findFormFields($E(elementName))
        for (i = 0; i < inputNodes.length; i++)
        {
            var node = inputNodes[i];
            if (node.type == "checkbox") {
                node.checked = false;
            }
        }
    }

    function unselectStatuses()
    {
        for (i = 0; i < document.filterOptionForm.statuses.length; i++)
        {
            document.filterOptionForm.statuses[i].checked=false;
        }
    }

    function selectAll()
    {
        if (!document.contribsForm.contributions.length)
        {
            document.contribsForm.contributions.checked=true
        }else{
            for (i = 0; i < document.contribsForm.contributions.length; i++)
            {
                document.contribsForm.contributions[i].checked=true;
            }
        }
        isSelected("contribsItems");
    }

    function deselectAll()
    {
        if (!document.contribsForm.contributions.length)
        {
            document.contribsForm.contributions.checked=false
        }else{
            for (i = 0; i < document.contribsForm.contributions.length; i++)
            {
                document.contribsForm.contributions[i].checked=false;
            }
        }
        isSelected("contribsItems");
    }

    var staticURLState = false;
    var staticURLSwitch = function() {
        if (staticURLState) {
            IndicoUI.Effect.disappear($E('staticURL'));
            IndicoUI.Effect.disappear($E('staticURLLink'));
        } else {
            IndicoUI.Effect.appear($E('staticURL'));
            IndicoUI.Effect.appear($E('staticURLLink'));
            $E('staticURL').dom.select();
        }
        staticURLState = !staticURLState;
    }

    window.onload = function(){
        isSelected("contribsItems");
    }
//-->
</script>

<table width="100%" cellspacing="0" align="center" border="0" style="padding-left:2px">
     <tr>
       <td nowrap colspan="10">
            <div class="CRLgroupTitleNoBorder"><%= _("Displaying")%><strong> <%= numContribs %> </strong>
            <% if numContribs == "1": %>
                <%= _("contribution")%>
            <% end %>
            <% else: %>
                <%= _("contributions")%>
            <% end %>
            <% if filterUsed: %>
                (<%= _("Total")%>: <strong><%= totalNumContribs %></strong>)
            <% end %>
        </div>
        <form action=<%= filterPostURL %> method="post" name="optionForm">
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
            <span style="padding: 0px 6px 0px 6px">|</span>
            <a id="index_display" onclick="staticURLSwitch()" class="CAIndexUnselected" font-size="16">
                <%= _("Static URL for this result")%>
            </a>
        </div>
        </form>
        </td>
     </tr>
     <tr>
        <td colspan="1000" align="left" width="100%">
          <form action=<%= filterPostURL %> method="post" name="filterOptionForm">
            <input type="hidden" name="operationType" value="filter" />
            <%= filterMenu %>
            <%= sortingOptions %>
          </form>
        </td>
    </tr>
    <tr>
        <td colspan="1000" align="left" width="100%">
            <input type="text" id="staticURL" size="74" style="display: none;" readonly="readonly" value="<%= filterUrl %>" />
            <a id="staticURLLink" style="display: none; margin-left: 5px;" href="<%= filterUrl %>"><%= _("Go to URL")%></a>
        </td>
    </tr>
    <tr>

        <td colspan="40" style="border-bottom: 2px solid #777777; padding-top: 3px;" valign="bottom" align="left">
            <form action=<%= contribSelectionAction %> method="post" name="contribsForm">
            <table>
                <tbody>

                        <td valign="bottom" align="left" class="eventModifButtonBar">
                            <input type="submit" class="btn" name="move" value="<%= _("Move")%>">
                        </td>
                        <td valign="bottom" align="left">
                            <input type="submit" class="btn" name="AUTH" value="<%= _("Author list")%>">
                        </td>
                        <td valign="bottom" align="left">
                            <input type="submit" class="btn" name="PKG" value="<%= _("Material package")%>">
                        </td>
                        <td valign="bottom" align="left">
                            <input type="submit" class="btn" name="PROC" value="<%= _("Proceedings")%>">
                        </td>
                        <td valign="middle" align="left">
                            <input type="image" src=<%= pdfIconURL%> class="btn" name="PDF" value="<%= _("Create PDF")%>" onclick='this.form.action=<%= contributionsPDFURL %>;this.form.target="_blank";'>
                        </td>
                </tbody>
            </table>
        </td>
    </tr>

    <tr>
      <td colspan="1000" align="left" width="100%">
        <table width="100%" cellspacing="0" border="0" align="center">
          <thead>
            <tr>
              <td colspan=4 style='padding: 5px 0px 10px;' nowrap>
                Select: <a style='color: #0B63A5;' alt='Select all' onclick='javascript:selectAll()'> All</a>,
                        <a style='color: #0B63A5;' alt='Unselect all' onclick='javascript:deselectAll()'>None</a>
              </td>
            </tr>
            <tr>
              <td></td>
              <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"><%= numberImg %><a href=<%= numberSortingURL %>> <%= _("Id")%></a></td>
              <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"><%= dateImg %><a href=<%= dateSortingURL %>> <%= _("Date")%></a></td>
              <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"><%= _("Duration")%></td>
              <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"><%= typeImg %><a href=<%= typeSortingURL %>> <%= _("Type")%></a></td>
              <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"><%= titleImg %><a href=<%= titleSortingURL %>> <%= _("Title")%></a></td>
              <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"><%= speakerImg %><a href=<%= speakerSortingURL %>> <%= _("Presenter")%></a></a></td>
              <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"><%= sessionImg %><a href=<%= sessionSortingURL %>> <%= _("Session")%></a></td>
              <td nowrap class="titleCellFormat" style="Border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"><%= trackImg %><a href=<%= trackSortingURL %>> <%= _("Track")%></a></td>
              <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> <%= _("Status")%></td>
              <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> <%= _("Material")%></td>
            </tr>
          </thead>
          <tbody id="contribsItems">
            <%= contributions %>
          </tbody>
          <tbody>
            <tr><td style="padding-top: 3px; border-top: 2px solid #777777;" colspan="11" align="center"><font color="black"> <%= _("Total duration of displayed contributions")%>: <b><%= totaldur %></b></font></td></tr>

            <tr>
                <td colspan="40" valign="bottom" align="left">
                    <table>
                        <tbody>

                                <td valign="bottom" align="left" class="eventModifButtonBar">
                                    <input type="submit" class="btn" name="move" value="<%= _("Move")%>">
                                </td>
                                <td valign="bottom" align="left">
                                    <input type="submit" class="btn" name="AUTH" value="<%= _("Author list")%>">
                                </td>
                                <td valign="bottom" align="left">
                                    <input type="submit" class="btn" name="PKG" value="<%= _("Material package")%>">
                                </td>
                                <td valign="bottom" align="left">
                                    <input type="submit" class="btn" name="PROC" value="<%= _("Proceedings")%>">
                                </td>
                                <td valign="middle " align="left">
                                    <input type="image" src=<%= pdfIconURL%> class="btn" name="PDF" value="<%= _("Create PDF")%>" onclick='this.form.action=<%= contributionsPDFURL %>;this.form.target="_blank";'>
                                </td>
                        </tbody>
                    </table>
                </td>
            </tr>
          </tbody>
        </table>
      </td>
    </tr>
</table>
</form>
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
        if(!newUser) {
            var inputNodes = IndicoUtil.findFormFields($E("contribsItems"))
            for (i = 0; i < inputNodes.length; i++)
            {
                var node = inputNodes[i];
                if (node.type == "checkbox") {
                    if(node.checked == true) {
                        return true;
                    }
                }
            }

            var dialog = new WarningPopup($T("Warning"), $T("No contribution selected! Please select at least one."));
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

<script type="text/javascript">
var parentEventRoomData = $O(<%= jsonEncode(roomInfo(self._rh._target)) %>);

var addContribution = function() {
    var dialog = new AddNewContributionDialog(
                       'schedule.event.addContribution',
                       null,
		       <%= jsonEncode({'conference': self._conf.id }) %>,
		       <%= jsonEncode({'location': locationName,
		       'room': roomName,
		       'address': address }) %>,
                       parentEventRoomData,
                       '',
                       '',
                       <%= jsBoolean(self._conf.getType() != 'meeting') %>,
                       [],
                       null,
                       null,
                       function() {
                          window.location.reload();
                       },
                       <%= jsBoolean(self._conf.getAbstractMgr().isActive()) %>,
                       <%= bookings %>
                       );

    dialog.execute();
};
</script>