<%namespace name="common" file="${context['INCLUDE']}/Common.tpl"/>
<%
    daysDict = {}
    if firstDay:
        _firstDay = getDate(parseDate(firstDay,format="%d-%B-%Y"))
    else:
        _firstDay = getDate(startDate)
    if lastDay:
        _lastDay = getDate(parseDate(lastDay,format="%d-%B-%Y"))
    else:
        _lastDay = getDate(endDate)
    for entry in entries:
        entryDate = getDate(entry.getAdjustedStartDate(timezone))
        eSD = entry.getAdjustedStartDate(timezone)
        if entryDate >= _firstDay and entryDate <= _lastDay:
            if not daysDict.has_key(entryDate):
                daysDict[entryDate] = {}
                daysDict[entryDate]['AM'] = []
                daysDict[entryDate]['PM'] = []
            dayDate = 'AM' if eSD.hour < 13 else 'PM'
            daysDict[entryDate][dayDate].append(entry)
    if not daysPerRow:
        numRows = 1
        _daysPerRow = len(daysDict)
    elif int(daysPerRow) == 0:
        numRows = 1
        _daysPerRow = len(daysDict)
    else:
        numRows = len(daysDict) / int(daysPerRow)
        numRows += 1 if len(daysDict) % int(daysPerRow) != 0 else 0
        _daysPerRow = int(daysPerRow)
%>

<%def name="printSession(item)" >

<% session = item.getSession()%>
    <tr>
    <td valign="top" bgcolor="#b0e0ff" width="5%">
    <span style="font-weight:bold;">${getTime(item.getAdjustedStartDate(timezone))}</span>
    </td>
    <td colspan="1" bgcolor="#90c0f0">
    <div style="float:right">
        <%include file="${INCLUDE}/ManageButton.tpl" args="item=item, alignRight=True"/>
    </div>
    <span style="font-weight:bold;">${session.getTitle()}</span>
    %  if len(item.getOwnConvenerList()) > 0 or session.getConvenerText():
    -<span style="color:green;">
           ${common.renderUsers(item.getOwnConvenerList(), unformatted=session.getConvenerText(), title=False, italicAffilation=False, separator=' ')}
     </span>
    % endif
    % if not isTime0H0M(session.getAdjustedStartDate(timezone)):
        (until ${getTime(item.getAdjustedEndDate(timezone))})
    % endif
    % if getLocationInfo(item) != getLocationInfo(item.getConference()):
        (${getLocationInfo(item)[1]})
    % endif
    <div style="float:right">
        % for material in session.getAllMaterialList():
                    % if material.canView(accessWrapper):
                    <%include file="${INCLUDE}/Material.tpl" args="material=material, sessionId=item.getId()"/>
                    % endif
        % endfor
    </div>
    </td>
    </tr>
    % if len(item.getSchedule().getEntries()) > 0:
        <% countContribs = 0 %>
        % for subitem in item.getSchedule().getEntries():
                <%
                    if subitem.__class__.__name__ != 'BreakTimeSchEntry':
                        subitem = subitem.getOwner()
                        if not subitem.canView(accessWrapper):
                            continue
                %>
            % if getItemType(subitem) == "Break":
                ${printBreak(subitem)}
            % elif getItemType(subitem) == "Contribution":
                ${printContribution(subitem, countContribs)}
                <% countContribs += 1 %>
            % endif
        % endfor
    % endif
</%def>


<%def name="printContribution(item, contribIndex)" >

    <tr bgcolor=${"silver" if contribIndex % 2 != 0 else "#D2D2D2"}>
        <td bgcolor=${"#D0D0D0" if contribIndex % 2 != 0 else "#E2E2E2"}  valign="top" width="5%">
            ${getTime(item.getAdjustedStartDate(timezone))}
        </td>
        <td valign="top">
                       &nbsp;${item.getTitle()}
                      % if item.getSpeakerList() or item.getSpeakerText():
                            - ${common.renderUsers(item.getSpeakerList(), unformatted=item.getSpeakerText(), title=False, spanClass='speakerList',italicAffilation=False, separator=' ')}
                      % endif
                  &nbsp;
                  <div style="float:right">
                      <div style="float:left">
                          % for material in item.getAllMaterialList():
                                    % if material.canView(accessWrapper):
                                    <%include file="${INCLUDE}/Material.tpl" args="material=material, contribId=item.getId()"/>
                                    % endif
                          % endfor
                      </div>
                      <div style="float:right">
                        <%include file="${INCLUDE}/ManageButton.tpl" args="item=item, alignRight=False"/>
                      </div>
                  </div>
        </td>
   </tr>
</%def>

<%def name="printBreak(item)" >
  <tr>
    <td valign="top" bgcolor="#FFdcdc">
        ${getTime(item.getAdjustedStartDate(timezone))}
    </td>
    <td valign="top" bgcolor="#FFcccc" align="center" colspan="1">
      ---&nbsp;${item.getTitle()}&nbsp;---
    </td>
  </tr>
</%def>

<table class= "eventHeader">
<tr>
    <td>
    <span style="font-weight:bold;">
    <%include file="${INCLUDE}/ManageButton.tpl" args="item=conf, manageLink=False, alignRight=False"/>
    ${conf.getTitle()}
    </span><br/>
    ${common.renderEventTimeCompact(startDate, endDate)}
    <br/><br/>
    </td>
    <td>
    <table class="headerLegendsBorder" cellpadding="1" align="right">
    <tr>
        <td>
            <table class="headerLegendsContent" cellpadding="2">
            <tr>
                <td>
                <table><tr><td class="sessionsLegend">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td><td class="titleClass">: Sessions</td></tr></table>
                </td>
                <td>

                <table cellspacing="0"><tr><td class="contribsLegendSilver">&nbsp;&nbsp;&nbsp;</td><td>/</td><td class="contribsLegendGrey">&nbsp;&nbsp;&nbsp;</td><td class="titleClass">: Talks</td></tr></table>

                </td>
                <td>

                <table><tr><td class="breaksLegend">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td><td class="titleClass">: Breaks</td></tr></table>

                </td>
            </tr>
            </table>
        </td>
    </tr>
    </table>
    </td>
</tr>
</table>

<center>

<table class="dayList" cellpadding="0">

% for i in range (0,numRows):
    <% contDays = 0 %>
    <tr>
        <td></td>
        % for day in sorted(daysDict.keys()):
        <td class="headerselected" align="center" bgcolor="#000060"><span style="color:white; font-weight:bold;">
            ${prettyDate(parseDate(day,"%Y-%m-%d"))}<br/>
        </td>
        <% contDays += 1%>
            % if contDays == _daysPerRow:
               <% break %>
            % endif
        % endfor
    </tr>
    <% contDays = 0 %>
    <tr bgcolor="white">
        <td valign="top" class="headerselected" bgcolor="#000060" width="30">
            <table width="100%" cellspacing="0" cellpadding="2" border="0">
                <tr>
                    <td align="center" class="headerselected" bgcolor="#000060">
                        <span style="font-size: x-small; font-weight:bold; color:white;" >
                        AM
                        </span>
                    </td>
                </tr>
            </table>
        </td>
        <% countContribs = 0 %>
        % for day in sorted(daysDict.keys()):
            <td valign="top" bgcolor="gray">
                <table width="100%" cellspacing="1" cellpadding="3" border="0">
                    % for item in daysDict[day]['AM']:
                                 % if getItemType(item) == "Session":
                                     ${printSession(item)}
                                 % elif getItemType(item) == "Contribution":
                                     ${printContribution(item, countContribs)}
                                     <% countContribs += 1 %>
                                 % elif getItemType(item) == "Break":
                                     ${printBreak(item)}
                                 % endif
                    % endfor
                </table>
            </td>
            <% contDays += 1%>
            % if contDays == _daysPerRow:
               <% break %>
            % endif
        % endfor
    </tr>
    <% contDays = 0 %>
    <tr>
        <td valign="top" class="headerselected" bgcolor="#000060">
            <table width="100%" cellspacing="0" cellpadding="2" border="0">
                <tr>
                    <td align="center" class="headerselected" bgcolor="#000060">
                        <span style="font-size: x-small; font-weight:bold; color:white;" >
                        PM
                        </span>
                    </td>
                </tr>
            </table>
        </td>

        % for day in sorted(daysDict.keys()):
            <td valign="top" bgcolor="gray">
                <table width="100%" cellspacing="1" cellpadding="3" border="0">
                    % for item in daysDict[day]['PM']:
                                 % if getItemType(item) == "Session":
                                     ${printSession(item)}
                                 % elif getItemType(item) == "Contribution":
                                     ${printContribution(item, countContribs)}
                                     <% countContribs += 1 %>
                                 % elif getItemType(item) == "Break":
                                     ${printBreak(item)}
                                 % endif
                    % endfor
                </table>
            </td>
            <% daysDict.pop(day) %>
            <% contDays += 1%>
            % if contDays == _daysPerRow:
               <% break %>
            % endif
        % endfor
    </tr>
% endfor

</table>
</center>

