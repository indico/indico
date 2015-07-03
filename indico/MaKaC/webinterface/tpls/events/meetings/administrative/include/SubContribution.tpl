<%page args="item, allMaterial=False, inlineMinutes=False, order=1, suborder=1"/>

<%namespace name="common" file="../../${context['INCLUDE']}/Common.tpl"/>
<%namespace name="base" file="../Administrative.tpl"/>

<tr>

    <td class="itemTopAlign" colspan="2">
        <table class="subItemOrder">
            <tr>
                <td class="itemTopAlign subItemOrder">
                    <span class="subItemText">&nbsp;&nbsp;&nbsp;${order}.${suborder}</span>
                </td>
                <td class="itemTopAlign">
                    <span class="subItemText">${item.getTitle()}</span>
                    % if inlineMinutes and item.note:
                        ${common.renderDescription(item.note.html)}
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

            % for folder in item.attached_items.get('folders', []):
                % if folder.title == 'document' and  item.getReportNumberHolder().listReportNumbers():
                    <% materialDocuments = True %>
                    <a href="${url_for('attachments.list_folder', folder, redirect_if_single=True)}">
                        % for rn in item.getReportNumberHolder().listReportNumbers():
                             ${rn[1]}
                        % endfor
                    </a><br>
                % endif
            % endfor

            % if not materialDocuments and item.getReportNumberHolder().listReportNumbers():
                % for rn in item.getReportNumberHolder().listReportNumbers():
                    ${rn[1]}<br/>
                % endfor
            % endif

            % if item.attached_items:
                ${base.render_materials(item, exclude_document=True)}
            % endif
        % else:
            % if item.attached_items:
                ${base.render_materials(item)}
            % endif
        % endif

        % if item.note:
            <a href="${ url_for('event_notes.view', item) }">${ _("Minutes") }</a>
        % endif
        </span>
    </td>

    <td class="itemTopAlign">
         <%include file="../../${INCLUDE}/ManageButton.tpl" args="item=item, alignRight=True, minutesToggle=False"/>
    </td>
</tr>
