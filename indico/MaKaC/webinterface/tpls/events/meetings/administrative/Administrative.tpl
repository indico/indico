<%page args="showOrder=True"/>
<%namespace name="common" file="../${context['INCLUDE']}/Common.tpl"/>
<%!
  allMaterial = False
  hideTime = True
  materialSession = False
  minutes = False
%>
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
            <%include file="../${INCLUDE}/ManageButton.tpl" args="item=conf, manageLink=False, alignRight=False"/>
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
            <br/>
        </div>

        % if conf.getDescription():
            <br/><br/>
            <span class="textTitle">Description: </span><br/><span class="descriptionText">${common.renderDescription(conf.getDescription())}</span>
        % endif

        % if participants:
            <br/><br/>
            <span class="textTitle">Participants: </span><br/><span class="participantText">${participants}</span>
        % endif

        <br/><br/>
        % if self.attr.minutes:
            <% minutesText = conf.getMinutes().getText() if conf.getMinutes() else None %>
            % if minutesText:
                ${common.renderDescription(minutesText)}
            % endif
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
                            <td class="itemHeaderDate" colspan="2">
                                ${prettyDate(item.getAdjustedStartDate(timezone))}<br />
                                <br />
                            </td>
                            <td class="itemHeaderDocuments" colspan="2">
                                Documents<br /><br />
                            </td>
                            <td></td>
                        </tr>
                    % endif
                    % if getItemType(item) == "Session":
                        <%include file="include/Session.tpl" args="item=item, parent=conf, hideTime=self.attr.hideTime, allMaterial=self.attr.allMaterial, materialSession=self.attr.materialSession, minutes=self.attr.minutes, showOrder=showOrder"/>
                    % else:
                        <%include file="include/${getItemType(item)}.tpl" args="item=item, parent=conf, hideTime=self.attr.hideTime, allMaterial=self.attr.allMaterial, materialSession=self.attr.materialSession, minutes=self.attr.minutes, order=order, showOrder=showOrder"/>
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
