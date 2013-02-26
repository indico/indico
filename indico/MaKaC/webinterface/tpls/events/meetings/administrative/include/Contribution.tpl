<%page args="item, parent, hideTime=False, allMaterial=False, minutes=False, order=1, showOrder=True" />

<%namespace name="common" file="../../${context['INCLUDE']}/Common.tpl"/>

<tr>
    <td colspan="4"></td>
</tr>
<tr>
    <td class="itemTopAlign itemLeftAlign ">
        % if showOrder:
            % if not hideTime:
                <span class="itemTime">${getTime(item.getAdjustedStartDate(timezone))}</span>&nbsp;&nbsp;${order}.
            % else:
                ${order}.
            % endif
        % elif not hideTime:
               <span class="itemTime">${getTime(item.getAdjustedStartDate(timezone))}</span>
        % endif

    </td>
    <td class="itemTopAlign itemLeftAlign">
        ${item.getTitle()}
        <br/>
        % if minutes:
            <% minutesText = item.getMinutes().getText() if item.getMinutes() else None %>
            % if minutesText:
                ${common.renderDescription(minutesText)}
            % endif
        % endif
        % if item.getDescription():
           <br/>
           ${common.renderDescription(item.getDescription())}
        % endif

    </td>
    <td class="itemTopAlign itemRightAlign">
        % if item.getSpeakerList() or item.getSpeakerText():
            <span class="participantText">
                ${common.renderUsers(item.getSpeakerList(), unformatted=item.getSpeakerText(), title=False, italicAffilation=True, separator=' ')}
            </span>
            <br/>
        % endif
        <span class="materialDisplayName">
        % if not allMaterial:
            <% materialDocuments = False %>
            % for material in item.getAllMaterialList():
                % if material.canView(accessWrapper):
                    % if material.getTitle()=='document' and item.getReportNumberHolder().listReportNumbers():
                        <%
                        materialDocuments = True
                        %>
                        <a href="${urlHandlers.UHMaterialDisplay.getURL(material)}">
                        % for rn in item.getReportNumberHolder().listReportNumbers():
                             ${rn[1]}
                        % endfor
                        </a><br/>
                    % endif
                % endif
            % endfor
            % if not materialDocuments and item.getReportNumberHolder().listReportNumbers():
                % for rn in item.getReportNumberHolder().listReportNumbers():
                    ${rn[1]}<br/>
                % endfor
            % endif
            % if len(item.getAllMaterialList()) > 0:
                % for material in item.getAllMaterialList():
                    % if material.canView(accessWrapper):
                        % if material.getTitle()!='document' or not item.getReportNumberHolder().listReportNumbers():
                            <a href="${urlHandlers.UHMaterialDisplay.getURL(material)}">${material.getTitle()}</a><br/>
                        % endif
                    % endif
                % endfor
            % endif
        % else:
            % if len(item.getAllMaterialList()) > 0:
                % for material in item.getAllMaterialList():
                    % if material.canView(accessWrapper):
                        <a href="${urlHandlers.UHMaterialDisplay.getURL(material)}">${material.getTitle()}</a><br/>
                    % endif
                % endfor
            % endif
        % endif
        </span>
    </td>
    <td class="itemTopAlign">
        <%include file="../../${INCLUDE}/ManageButton.tpl" args="item=item, alignRight=True"/>
    </td>
</tr>
% if item.getSubContributionList():
    <% suborder = 1 %>
    % for subcont in item.getSubContributionList():
        <%include file="SubContribution.tpl" args="item=subcont, allMaterial=allMaterial, minutes=minutes, order = order, suborder=suborder"/>
        <% suborder += 1 %>
    % endfor
% endif