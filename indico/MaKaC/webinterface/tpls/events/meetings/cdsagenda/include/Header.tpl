<%page/>
<%namespace name="common" file="../../${context['INCLUDE']}/Common.tpl"/>

<table width="100%" border="0" bgcolor="white" cellpadding="1" cellspacing="1">
<tr>
  <td valign="top" align="left">
    <table border="0" bgcolor="gray" cellspacing="1" cellpadding="1" width="100%">
    <tr>
      <td colspan="1">
    <table border="0" cellpadding="2" cellspacing="0" width="100%" class="headerselected" bgcolor="#000060">
    <tr>
          <td width="35">
            <img src="${Config.getInstance().getBaseURL()}/images/meeting.png" width="32" height="32" alt="lecture"/>
          </td>
          <td class="headerselected">
            <span class="confTitle" style="font-weight:bold;">
                ${conf.getTitle()}
            </span>
            <div style="float: right; height: 15px;">
                <%include file="../../${INCLUDE}/ManageButton.tpl" args="item=conf, manageLink=False, alignRight=True, minutesToggle=False, minutesEditActions=True"/>
            </div>
            % if conf.getReportNumberHolder().listReportNumbers():
                <span style="font-size:x-small;">
                    % for reportNumber in conf.getReportNumberHolder().listReportNumbers():
                        <br/><a style="color:#FFFFFF;" href="${reportNumberSystems[reportNumber[0]]["url"] + reportNumber[1]}" target="_blank">${reportNumber[1]} </a>
                    % endfor
                </span>
            % endif
          </td>
        </tr>
        </table>
      </td>
    </tr>
    <tr>
      <td>
        <table border="0" bgcolor="#f0c060" cellpadding="2" cellspacing="0" width="100%" >
        <tr>
          <td valign="top" align="right"  class="headerTitle">
              Date/Time:
          </td>
          <td style="width:90%" class="headerInfo">
            ${common.renderEventTime2(startDate, endDate, timezone)}
          </td>
        </tr>
        % if getLocationInfo(conf) != ('', '', ''):
        <tr>
          <td valign="top" align="right"  class="headerTitle">
            Location:
          </td>
          <td class="headerInfo">
               ${common.renderLocation(conf)}
          </td>
        </tr>
        % endif

        % if conf.getChairList() or conf.getChairmanText():
        <tr>
          <td valign="top" align="right"  class="headerTitle">
            Chairperson:
          </td>
          <td class="headerInfo">
             ${common.renderUsers(conf.getChairList(), unformatted=conf.getChairmanText(), spanClass='', title=False)}
          </td>
        </tr>
        % endif

        % if conf.getSupportInfo().getEmail():
        <tr>
          <td valign="top" align="right"  class="headerTitle">
                  ${supportEmailCaption}
          </td>
          <td class="headerInfo">
                  ${conf.getSupportInfo().getEmail()}
          </td>
        </tr>
        % endif

        % if conf.getDescription():
        <tr>
          <td valign="top" align="right"  class="headerTitle">
            Description:
          </td>
          <td class="fixPreOverflow" class="headerInfo">
            ${common.renderDescription(conf.getDescription())}
          </td>
        </tr>
        %endif

        <%
        from indico.modules.events.registration.util import get_published_registrations
        participants = get_published_registrations(conf)
        %>
        % if participants:
        <tr>
          <td valign="top" align="right" class="headerTitle">
            Participants:
          </td>
          <td class="headerInfo" style="font-style:italic;">
            <ul class="participant-list">
              % for participant in participants:
                <li>${ participant.full_name }</li>
              % endfor
            </ul>
          </td>
        </tr>
        % endif
        % if conf.attached_items:
         <tr>
          <td valign="top" align="right" class="headerTitle icon-attachment inline-attachments-icon"></td>
          <td class="material-list">
            ${ render_template('attachments/mako_compat/attachments_inline.html', item=conf) }
          </td>
        </tr>
        % endif
        % if conf.note:
            <tr>
                <td valign="top" align="right" class="headerTitle">
                    ${ _("Minutes") }:
                </td>
                <td>
                    <a href="${ url_for('event_notes.view', conf) }">
                        ${ _("Download") }
                    </a>
                </td>
            </tr>
        % endif
        </table>
      </td>
    </tr>
    </table>
  </td>
  <td align="right" valign="top">
    <table border="0" bgcolor="gray" cellspacing="1" cellpadding="1">
        % if conf.getNumberOfSessions() !=0:
            <tr>
                <td>
                    <table bgcolor="white" cellpadding="2" cellspacing="0" border="0" width="100%">
                        <% contSessions = 0 %>
                        % for item in entries:
                            % if getItemType(item)=="Session":
                            <% session = item.getSession() %>
                                <tr>
                                    <td valign="top" class="headerselected" bgcolor="#000060">
                                        <span style="font-size:x-small;color:white;">
                                            % if getDate(session.getAdjustedStartDate(timezone)) == getDate(session.getAdjustedEndDate(timezone)):
                                                ${prettyDate(session.getAdjustedStartDate(timezone))}&nbsp;${getTime(session.getAdjustedStartDate(timezone))}
                                                % if not isTime0H0M(session.getAdjustedEndDate(timezone)):
                                                    ->${getTime(session.getAdjustedEndDate(timezone))}
                                                % endif
                                            % else:
                                                ${prettyDate(session.getAdjustedStartDate(timezone))}&nbsp;${getTime(session.getAdjustedStartDate(timezone))}->${prettyDate(session.getAdjustedEndDate(timezone))}&nbsp;${getTime(session.getAdjustedEndDate(timezone))}
                                            % endif
                                        </span>
                                    </td>
                                    <% bgcolor="#E4E4E4" if contSessions % 2 == 1 else "#F6F6F6" %>
                                    <td valign="top" bgcolor=${bgcolor}>
                                    <a href="#${session.getId()}">
                                        <span style="font-size:x-small">
                                            ${session.getTitle() if session.getTitle!='' else "no title"}
                                        </span>
                                    </a>
                                    <span style="font-size:x-small">
                                        % if getLocationInfo(item)!= getLocationInfo(conf):
                                           (${getLocationInfo(item)[1]})

                                        % endif
                                    </span>
                                    &nbsp;
                                    </td>

                                    <td valign="top" align="right" bgcolor=${bgcolor}>&nbsp;</td>
                                </tr>
                            <% contSessions +=1 %>
                            % endif
                            % endfor
    </table>
    </td></tr>
    % endif
</table>
    </td>
</tr>
</table>
