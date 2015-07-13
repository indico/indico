<%page args="item, parent, hideTime=False, allMaterial=False, inlineMinutes=False, order=1, showOrder=True" />

<%namespace name="common" file="../../${context['INCLUDE']}/Common.tpl"/>
<%namespace name="base" file="../Administrative.tpl"/>

<tr>
    <td colspan="4"></td>
</tr>
<tr>
    <td class="itemTopAlign itemLeftAlign ">
        % if showOrder:
            % if not hideTime:
                <span class="itemTime">${getTime(item.getAdjustedStartDate(timezone))}</span>
                <span class="itemIndex">&nbsp;&nbsp;${ order }.</span>
            % else:
                ${order}.
            % endif
        % elif not hideTime:
               <span class="itemTime">${getTime(item.getAdjustedStartDate(timezone))}</span>
        % endif

    </td>
    <td class="itemTopAlign itemLeftAlign itemTitle">
        ${item.getTitle()}<br/>
        % if item.getDescription():
           ${common.renderDescription(item.getDescription())}
        % endif
        % if inlineMinutes and item.note:
            ${common.renderDescription(item.note.html)}
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
        <%include file="../../${INCLUDE}/ManageButton.tpl" args="item=item, alignRight=True, minutesToggle=False, minutesEditActions=True"/>
    </td>
</tr>
% if item.getSubContributionList():
    <% suborder = 1 %>
    % for subcont in item.getSubContributionList():
        <%include file="SubContribution.tpl" args="item=subcont, allMaterial=allMaterial, inlineMinutes=inlineMinutes, order = order, suborder=suborder"/>
        <% suborder += 1 %>
    % endfor
% endif
