<%page args="item, parent=None, minutes=False, checkStartTime=False, checkEndTime=False, olist=False, order=0, showDescriptionTitle=False,checkOwnerLocation=True"/>
<%namespace name="common" file="../../${context['INCLUDE']}/Common.tpl"/>

<% session = item.getSession() %>

<a name="${session.getId()}"></a>
<table width="100%" cellpadding="1" cellspacing="0" border="0">
<tr class="headerselected" bgcolor="#000060">
  <td valign="top" class="headerselected" align="left">

    <span style="font-size:large; font-family:Arial; color:white; font-weight:bold;">
    % if item.getTitle() != "" and item.getTitle() != session.getTitle():
        ${session.getTitle()}: ${item.getTitle()}
    % else:
        ${session.getTitle()}
    % endif
    </span>
    <span class="headerInfo">
    (${getTime(item.getAdjustedStartDate(timezone))}
    % if (checkEndTime and not isTime0H0M(item.getAdjustedEndDate(timezone))) or not checkEndTime:
    ->${getTime(item.getAdjustedEndDate(timezone))}
    % endif
    )
    </span>
  </td>
  <td valign="top" align="right">
    % if session.getDescription() or len(item.getOwnConvenerList()) > 0 or session.getConvenerText() or (getLocationInfo(item) != getLocationInfo(item.getOwner()) and checkOwnerLocation) or (getLocationInfo(item) != ('', '', '') and not checkOwnerLocation) or len(session.getAllMaterialList()) > 0:
    <table bgcolor="#f0c060" cellpadding="2" cellspacing="0" border="0" class="results">
    % if session.getDescription():
      <tr>
      % if showDescriptionTitle:
          <td valign="top" class="headerTitle">
            Description:
          </td>
          <td valign="top" colspan="2" width="400"  style="text-align: justify">
            ${common.renderDescription(session.getDescription())}
          </td>
      % else:
          <td valign="top" colspan="2" width="400"  style="text-align: justify; font-style:italic; font-size:x-small;">
            <i><small>${common.renderDescription(session.getDescription())}
          </td>
      % endif
      </tr>

    % endif
    % if len(item.getOwnConvenerList()) > 0 or session.getConvenerText():
    <tr>
      <td valign="top" class="headerTitle">
        Chairperson:
      </td>
      <td class="headerInfo" >
        ${common.renderUsers(item.getOwnConvenerList(), unformatted=session.getConvenerText(), title=False )}
      </td>
    </tr>
    % endif

    % if (getLocationInfo(item) != getLocationInfo(item.getOwner()) and checkOwnerLocation) or (getLocationInfo(item) != ('', '', '') and not checkOwnerLocation):
    <tr>
      <td valign="top" class="headerTitle">
        Location:
      </td>
      <td class="headerInfo" >
        ${common.renderLocation(item, parent=item.getConference())}
      </td>
    </tr>
    % endif
    % if len(session.getAllMaterialList()) > 0:
    <tr>
      <td valign="top" class="headerTitle">
        Material:
      </td>
      <td class="headerInfo" >
        % for material in session.getAllMaterialList():
            % if material.canView(accessWrapper):
                <%include file="../../${INCLUDE}/Material.tpl" args="material=material"/>
            % endif
        % endfor
      </td>
    </tr>
    % endif
    </table>
    % else:
    &nbsp;
    % endif
  </td>
  <td style="padding-right:4px; width:23px">
      <%include file="../../${INCLUDE}/ManageButton.tpl" args="item=item, alignRight=True"/>
  </td>
</tr>
</table>

% if len(item.getSchedule().getEntries()) > 0:
    <% subentries = item.getSchedule().getEntries()%>
    <table  width="100%" cellpadding="4" cellspacing="0" border="0">
    % for subindex, subitem in enumerate(subentries):
        <%
           if subitem.__class__.__name__ != 'BreakTimeSchEntry':
               subitem = subitem.getOwner()
               if not subitem.canView(accessWrapper):
                    continue
        %>
        <%include file="${getItemType(subitem)}.tpl"
            args="item=subitem, parent=item, minutes=minutes, olist=olist, order=order"/>
        % if getItemType(subitem) == 'Contribution':
            <%order+=1%>
        % endif
    % endfor

    </table>
% endif
<br/>