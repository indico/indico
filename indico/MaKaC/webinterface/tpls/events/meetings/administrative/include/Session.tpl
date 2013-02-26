<%page args="item, parent=None, allMaterial=False, hideTime=True, materialSession=False, order=1, showOrder=True"/>

<%namespace name="common" file="../../${context['INCLUDE']}/Common.tpl"/>

<% session = item.getSession() %>

<% conf = item.getConference() %>

<tr>
    <td>
        <%include file="../../${INCLUDE}/ManageButton.tpl" args="item=item, alignRight=True"/>
    </td>
    <td class="itemLeftAlign sessionInfo" colspan="2"><br/>
        <span class="sessionTitle">
            ${session.getTitle()}
        </span>
        % if getLocationInfo(item) == getLocationInfo(parent):
            (${common.renderLocationAdministrative(parent)})
        % elif getLocationInfo(item)!=('','',''):
            (${common.renderLocationAdministrative(item)})
        % endif
        <br/>
    </td>
    <td class="itemRightAlign" >
        <span class="materialDisplayName">
        % if len(session.getAllMaterialList()) > 0 and allMaterial:
            % for material in session.getAllMaterialList():
                % if material.canView(accessWrapper):
                    <a href="${urlHandlers.UHMaterialDisplay.getURL(material)}">${material.getTitle()}</a>&nbsp;
                % endif
            % endfor
        % elif materialSession and len(session.getAllMaterialList()) > 0:
            % for material in session.getAllMaterialList():
                % if material.canView(accessWrapper):
                    % if material.getTitle()!='document' or not conf.getReportNumberHolder().listReportNumbers():
                        <a href="${urlHandlers.UHMaterialDisplay.getURL(material)}">${material.getTitle()}</a>
                    % endif
                % endif
            % endfor
        % endif
        </span>
    </td>

</tr>
<tr>
    <td class="itemLeftAlign sessionInfo" colspan="4">
        <hr width="100%"/>
        % if session.getDescription():
            ${session.getDescription()}
            <hr width="100%"/>
        % endif
    </td>
</tr>

% if len(item.getSchedule().getEntries()) > 0:
    <% subentries = item.getSchedule().getEntries()%>

    % for subindex, subitem in enumerate(subentries):
        <%
            if subitem.__class__.__name__ != 'BreakTimeSchEntry':
                subitem = subitem.getOwner()
                if not subitem.canView(accessWrapper):
                    continue
        %>
        <%include file="${getItemType(subitem)}.tpl" args="item=subitem, parent=item, hideTime=hideTime, order=order, showOrder=showOrder"/>
        % if getItemType(subitem) == "Contribution":
            <% order +=1 %>
        % endif
    % endfor

% endif
