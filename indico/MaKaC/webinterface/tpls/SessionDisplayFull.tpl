<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% import MaKaC.common.timezoneUtils as timezoneUtils %>
<% import MaKaC.webinterface.linking as linking %>
<% from MaKaC.common.timezoneUtils import DisplayTZ %>
<% from indico.util.date_time import format_date, format_time, format_datetime %>
<% from pytz import timezone %>

<div id="buttonBar" class="sessionButtonBar">
    % if session.canModify(self_._aw):
        <a href="${str(urlHandlers.UHSessionModification.getURL(session))}" style="font-weight: bold" >${_("Edit")}</a> |
    % endif
    <% pdfUrl = urlHandlers.UHConfTimeTablePDF.getURL(session.getConference()) %>
    <% pdfUrl.addParam("showSessions", session.getId()) %>
    <a href="${str(pdfUrl)}" target="_blank">${_("PDF")}</a> |
    <a href="#" id="exportIcal${session.getUniqueId()}" class="fakeLink exportIcal" data-id="${session.getUniqueId()}"> ${_("iCal")}</a>
    <%include file="SessionICalExport.tpl" args="item=session"/>
</div>
<h1 class="sessionTitle">
    ${session.getTitle()}
</h1>
<div class="sessionMainContent abstractMainContent">
    <div class="sessionRightPanel abstractRightPanel">
        <% location = session.getLocation() %>
        <% room = session.getRoom() %>
        % if (room and room.getName()) or location:
            <div class="sessionRightPanelSection">
                <h2 class="sessionSectionTitle">${_("Place")}</h2>
                <div>
                % if location:
                    <div><span style="font-weight:bold">${_("Location")}: </span>${location.getName()}</div>
                    % if location.getAddress() is not None and location.getAddress() != "":
                        <div><span style="font-weight:bold">${_("Address")}: </span>${location.getAddress()}</div>
                    % endif
                % endif
                % if room and room.getName():
                    <div><span style="font-weight:bold">${_("Room")}: </span>${linking.RoomLinker().getHTMLLink(room, location)}</div>
                % endif
                </div>
            </div>
        % endif
        <% canEditFiles = self_._aw.getUser() and session.canModify(self_._aw) %>
        % if session.getAllMaterialList() or canEditFiles:
            <div class="sessionRightPanelSection" style="border: none;">
                <h2 class="sessionSectionTitle">${_("Files")}</h2>
                    % if canEditFiles:
                        <div style="float:right; line-height: 17px">
                            <a class="fakeLink" id="manageMaterial">${_("Edit files")}</a>
                        </div>
                    % endif
                <ul>
                % for material in session.getAllMaterialList():
                    <% if not material.canView(self_._aw):
                        continue
                    %>
                    <li><a href="${urlHandlers.UHMaterialDisplay.getURL(material)}" class="titleWithLink" title="${material.getDescription()}">${material.getTitle()}</a>
                        <ul class="subList">
                         % for resource in material.getResourceList():
                            <li><a href="${urlHandlers.UHFileAccess.getURL(resource)}" target="_blank" title="${resource.getDescription()}">${getResourceName(resource)}</a></li>
                         % endfor
                        </ul>
                    </li>
                % endfor
                </ul>
            </div>
        % endif
    </div>
    <div class="sessionLeftPanel">
        <div class="sessionInformation">
            <div class="sessionDateInformation">
                <% tzUtil = timezoneUtils.DisplayTZ(self_._aw, session.getOwner()) %>
                <% tz = tzUtil.getDisplayTZ() %>
                <% sDate = session.getAdjustedStartDate(tz) %>
                <% eDate = session.getAdjustedEndDate(tz) %>
                ${_("Date")}:
                % if sDate.date() == eDate.date():
                    <span style="font-weight: bold"> ${format_datetime(sDate, format='d MMM HH:mm')} - ${format_time(eDate)}</span>
                % else:
                    ${_("from")} <span style="font-weight: bold">${format_datetime(sDate, 'd MMM HH:mm')} </span> ${_("to")} <span style="font-weight: bold">${format_datetime(eDate, 'd MMM HH:mm')}</span>
                % endif
            </div>
        </div>
    </div>
    <div class="sessionLeftPanel">
        % if session.getDescription():
            <div class="sessionSection">
                <h2 class="sessionSectionTitle">${_("Description")}</h2>
                <div class="sessionSectionContent">${session.getDescription()}</div>
            </div>
        % endif
        % if slotConveners:
            <div class="sessionSection">
                <h2 class="sessionSectionTitle">${_("Conveners")}</h2>
                <div class="sessionSectionContent" style="white-space: normal">
                    <ul class="conveners">
                    % for slot in slotConveners:
                      <li>
                        <span class="time">
                          % if sDate.date() != eDate.date():
                            ${format_datetime(slot['startDate'], 'd MMM HH:mm')} - ${format_time(slot['endDate'])}
                          % endif
                        </span>
                        % if slot['title']:
                          <span class="title">
                            ${slot['title']}
                          </span>
                        % endif
                        <ul class="names">
                          % for convener in slot['conveners']:
                          <li>
                            % if self_._aw.getUser():
                              <a href="mailto:${convener['email']}">${convener['fullName']}</a>
                            % else:
                              <span>${convener['fullName']}</span>
                            % endif
                            % if convener['affiliation']:
                              <span class="affiliation"> (${convener['affiliation']})</span>
                            % endif
                          </li>
                          % endfor
                        </ul>
                      </li>
                    % endfor
                    </ul>
                </div>
            </div>
        % endif
    </div>
</div>
<div class="sessionContributionsSection">
    <div class="sessionContributionsSectionTitle">
        <h2 class="sessionSectionTitle">
            % if session.getScheduleType() == "poster":
                ${_("Contribution List")}
            % else:
                <span id="timeTableTitle" class="fakeLink">${_("Timetable")}</span><span> | </span><span id="contribListTitle" class="fakeLink">${_("Contribution List")}</span>
            % endif
        </h2>
    </div>

    <div id="contributionListDiv">
        <%include file="SessionContributionList.tpl" args="accessWrapper=self_._aw, poster=session.getScheduleType() == 'poster'"/>
    </div>
    % if session.getScheduleType() != "poster":
        <div id="timeTableDiv">
            <div class="timetablePreLoading" style="width: 700px; height: 300px">
                <div class="text" style="padding-top: 200px">${_("Building timetable...")}</div>
            </div>
            <div class="clearfix"></div>
        </div>
    % endif
</div>

<script type="text/javascript">
  var ttdata = ${ttdata | n,j};
  var eventInfo = ${eventInfo | n,j};

  $(function() {
    % if session.getScheduleType() != "poster":
        var timetable = new SessionDisplayTimeTable(ttdata, eventInfo, 710, $E('timeTableDiv'), new BrowserHistoryBroker());
        $E('timeTableDiv').set(timetable.draw());
        timetable.postDraw();
        $("#timeTableTitle").click(function(){
            $("#contribListTitle").css('font-weight','normal');
            $("#timeTableTitle").css('font-weight','bold');
            $('#contributionListDiv').hide();
            $('#timeTableDiv').show();
        });
        $("#timeTableTitle").click();
    % endif

    $("#contribListTitle").click(function(){
        $("#contribListTitle").css('font-weight','bold');
        $("#timeTableTitle").css('font-weight','normal');
        $('#contributionListDiv').show();
        $('#timeTableDiv').hide();
    });

    $("#manageMaterial").click(function(){
      IndicoUI.Dialogs.Material.editor(${session.getConference().getOwner().getId() |n,j},
                                       ${session.getConference().getId() |n,j}, ${session.getId() |n,j},'','',
                                       ${session.getAccessController().isProtected() |n,j},
                                       ${session.getMaterialRegistry().getMaterialList(session.getConference()) |n,j},
                                       ${'Indico.Urls.UploadAction.session'}, true);
    });
    $('.sessionRightPanel').css('height', $('.sessionMainContent').css('height'));
  });
</script>
