<%page args="showOrder=True"/>
<%namespace name="common" file="../${context['INCLUDE']}/Common.tpl"/>
<%!
  allMaterial = False
  hideTime = True
  materialSession = False
  minutes = False
  print_mode = False
%>

<%def name="render_materials(item, exclude_document=False)">
    % if item.attached_items:
        % for folder in item.attached_items['folders']:
            % if not exclude_document or folder.title != 'document':
                <a href="${url_for('attachments.list_folder', folder, redirect_if_single=True)}">${folder.title}</a>&nbsp;
            % endif
        % endfor
        % for file in item.attached_items['files']:
            <a href="${file.download_url}">${file.title}</a>&nbsp;
        % endfor
    % endif
</%def>

<table class="eventWrapper">
    <tr>
        <td>
            <div class="reportNumberHeader">
                % for rn in conf.getReportNumberHolder().listReportNumbers():
                    ${rn[1]}<br/>
                % endfor
            </div>

        <%block name="header">
            <br/>&nbsp;<br/>
            <div class="eventHeader">
                ORGANISATION EUROP&Eacute;ENNE POUR LA RECHERCHE NUCL&Eacute;AIRE<br/>
                <span class="CERNTitle"> CERN </span>
                EUROPEAN ORGANIZATION FOR NUCLEAR RESEARCH
            </div>
            <div align="center">
                <hr width="50%"/>
            </div>
        </%block>

        <br/>&nbsp;<br/>

        <div class="eventInfo">
            <%include file="../${INCLUDE}/ManageButton.tpl" args="item=conf, manageLink=False, alignRight=False, minutesToggle=False, minutesEditActions=True"/>
            ${conf.getTitle()}<br/>
            <%block name="locationAndTime">
                % if getLocationInfo(conf) != ('', '', ''):
                    ${common.renderLocationAdministrative(conf)}
                % endif
                ${common.renderEventTime2(startDate, endDate)}
            </%block>
            <br/>
            <%block name="eventMaterial">
            </%block>
            % if conf.note:
                <a href="${ url_for('event_notes.view', conf) }">${ _("Minutes") }</a>
            % endif
            <br/>
        </div>

        % if conf.getDescription():
            <br/><br/>
            <span class="textTitle">Description: </span><br/><span class="descriptionText">${common.renderDescription(conf.getDescription())}</span>
        % endif

        <%
        from indico.modules.events.registration.util import get_unique_published_registrations
        participants = get_unique_published_registrations(conf)
        %>
        % if participants:
            <br/><br/>
            <span class="textTitle">Participants: </span><br>
            <span class="participantText">${', '.join(reg.full_name for reg in participants)}</span>
        % endif

        <br/><br/>

        % if self.attr.minutes and conf.note:
            ${ common.renderDescription(conf.note.html) }
        % endif

        <%block name="printSchedule" args="showOrder=True">
            <table class="dayList">
                <% order = 1 %>
                % for index, item in enumerate(entries):
                    <%
                        date = getDate(item.getAdjustedStartDate(timezone))
                        previousItem = entries[index - 1] if index - 1 >= 0 else None
                        nextItem = entries[index + 1] if index + 1 < len(entries) else None
                    %>
                    % if (not previousItem or date != getDate(previousItem.getAdjustedStartDate(timezone))):
                        <tr></tr>
                        <tr>
                            <td class="itemHeaderDate" colspan="${ 4 if self.attr.print_mode else 2}">
                                <span>
                                    ${prettyDate(item.getAdjustedStartDate(timezone))}
                                </span>
                                <br />
                                <br />
                            </td>
                            % if not self.attr.print_mode:
                                <td class="itemHeaderDocuments" colspan="2">
                                    Documents<br /><br />
                                </td>
                                <td></td>
                            % endif
                        </tr>
                    % endif
                    % if getItemType(item) == "Session":
                        <%include file="include/Session.tpl" args="item=item, parent=conf, hideTime=self.attr.hideTime, allMaterial=self.attr.allMaterial, materialSession=self.attr.materialSession, inlineMinutes=self.attr.minutes, showOrder=showOrder, print_mode=self.attr.print_mode"/>
                    % else:
                        <%include file="include/${getItemType(item)}.tpl" args="item=item, parent=conf, hideTime=self.attr.hideTime, allMaterial=self.attr.allMaterial, materialSession=self.attr.materialSession, inlineMinutes=self.attr.minutes, order=order, showOrder=showOrder"/>
                    % endif
                    % if getItemType(item) != "Break":
                        <% order +=1 %>
                    % endif
                % endfor
            </table>
        </%block>
        <br/>
        </td>
    </tr>
</table>
