<%page args="item, allMaterial=False, minutes=False, order=1, suborder=1"/>

<%namespace name="common" file="../../${context['INCLUDE']}/Common.tpl"/>

<tr>

    <td class="itemTopAlign" colspan="2">
        <table class="subItemOrder">
            <tr>
                <td class="itemTopAlign subItemOrder">
                    <span class="subItemText">&nbsp;&nbsp;&nbsp;${order}.${suborder}</span>
                </td>
                <td class="itemTopAlign">
                    <span class="subItemText">${item.getTitle()}</span>
                    % if minutes:
                        <% minutesText = item.getMinutes().getText() if item.getMinutes() else None %>
                        % if minutesText:
                            ${common.renderDescription(minutesText)}
                        % endif
                    % endif
                </td>
            </tr>
        </table>
    </td>
    <td class="itemTopAlign itemRightAlign">
        % if item.getSpeakerList() or item.getSpeakerText():
            ${common.renderUsers(item.getSpeakerList(), unformatted=item.getSpeakerText())}
            <br/>
        % endif
        <span class="materialDisplayName">
        % if not allMaterial:
            <% materialDocuments = False %>
            % for material in item.getAllMaterialList():
                % if material.canView(accessWrapper):
                     % if material.getTitle()=='document' and item.getReportNumberHolder().listReportNumbers():
                     <% materialDocuments = True %>
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
