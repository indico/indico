<%page args="item, parent=None, allMaterial=False, hideTime=True, materialSession=False, order=1, showOrder=True, print_mode=False, inlineMinutes=False"/>

<%namespace name="common" file="../../${context['INCLUDE']}/Common.tpl"/>
<%namespace name="base" file="../Administrative.tpl"/>


<% session = item.getSession() %>

<% conf = item.getConference() %>

<tr>
    <td class="itemLeftAlign sessionInfo" colspan="${3 if print_mode else 2}">
        <span class="sessionTitle">
            ${session.getTitle()}
        </span>
        % if getLocationInfo(item) == getLocationInfo(parent):
            <span class="locationInfo">
                <span class="locationParenthesis">(</span>
                ${common.renderLocationAdministrative(parent)}
                <span class="locationParenthesis">)</span>
            </span>
        % elif getLocationInfo(item)!=('','',''):
            <span class="locationInfo">
                <span class="locationParenthesis">(</span>
                ${common.renderLocationAdministrative(item)}
                <span class="locationParenthesis">)</span>
            </span>
        % endif
    </td>
    <td class="itemRightAlign" >
        <span class="materialDisplayName">
        % if allMaterial:
            ${base.render_materials(conf)}
        % elif materialSession:
            % for material in session.attached_items.get('files', []):
                % if material.title != 'document' or not conf.getReportNumberHolder().listReportNumbers():
                    <a href="${material.download_url}">${material.title}</a>
                % endif
            % endfor
        % endif
        % if item.note:
            <a href="${ url_for('event_notes.view', item) }">${ _("Minutes") }</a>
        % endif
        </span>
    </td>
    % if not print_mode:
    <td>
        <%include file="../../${INCLUDE}/ManageButton.tpl" args="item=item, alignRight=True, minutesToggle=False"/>
    </td>
    % endif
</tr>
<tr>
    <td class="itemLeftAlign sessionInfo sessionDescription" colspan="4">
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
        <%include file="${getItemType(subitem)}.tpl" args="item=subitem, parent=item, hideTime=hideTime, order=order, showOrder=showOrder, inlineMinutes=inlineMinutes"/>
        % if getItemType(subitem) == "Contribution":
            <% order +=1 %>
        % endif
    % endfor

% endif
