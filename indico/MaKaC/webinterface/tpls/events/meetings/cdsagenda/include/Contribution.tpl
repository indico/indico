<%page args="item, parent, minutes=False, olist=False, order=0"/>

<%namespace name="common" file="../../${context['INCLUDE']}/Common.tpl"/>

<tr>
  <td valign="top" width="2%" style="font-weight:bold;">
    &nbsp;${getTime(item.getAdjustedStartDate(timezone))}
    % if olist:
      &nbsp;${order}.
    % endif
  </td>
  % if getLocationInfo(item) != getLocationInfo(parent):
  <td align="center" valign="top" class="header" width="1%">
      (${common.renderLocation(item, parent=parent)})
  </td>
  % else:
      <td width="1%" align="center" valign="top"></td>
  % endif
  <% bgcolor="#E4E4E4" if order % 2 == 0 else "#F6F6F6" %>
  <td colspan="2" width="75%" valign="top" bgcolor="${bgcolor}">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="${bgcolor}">
    <tr>
      <td valign="top" align="left">
        % if item.attached_items:
          <span class="material-list">
              ${ render_template('attachments/mako_compat/attachments_inline.html', item=item) }
          </span>
        % endif

        <span class="headline">${item.getTitle()}</span>
        % if item.getDuration():
             <span class="itemDuration"> (${prettyDuration(item.getDuration())}) </span>
        % endif
        % if item.getReportNumberHolder().listReportNumbers():
            (
            % for reportNumber in item.getReportNumberHolder().listReportNumbers():
                % if reportNumberSystems[reportNumber[0]]["url"]:
                    <a href="${reportNumberSystems[reportNumber[0]]["url"] + reportNumber[1]}" target="_blank">${reportNumber[1]} </a>
                % else:
                    ${reportNumber[1]}
                % endif
            % endfor
            )
        % endif
        &nbsp;
      </td>
      <td align="right">
          % if item.getSpeakerList() or item.getSpeakerText():
             ${common.renderUsers(item.getSpeakerList(), unformatted=item.getSpeakerText(), title=False, italicAffilation=false, separator=' ')}
          % endif
          % if item.note:
            <a href="${ url_for('event_notes.view', item) }">
                ${ _("Minutes") }
            </a>
          % endif
          &nbsp;
          <div style="float:right;">
             <%include file="../../${INCLUDE}/ManageButton.tpl" args="item=item, alignRight=True, minutesToggle=False, minutesEditActions=True"/>
          </div>
      </td>
    </tr>

    % if item.getDescription():
    <tr>
      <td colspan="3" style="text-align: justify">
        ${common.renderDescription(item.getDescription())}
      </td>
    </tr>
    % endif
    % if minutes and item.note:
        <tr>
        <td align="center" style="padding-top:10px;padding-bottom:10px" colspan="2">
          <table border="1" bgcolor="white" cellpadding="2" align="center" width="100%">
            <tr>
              <td align="center" style:"font-weight:bold;">${_("Minutes")}</td>
            </tr>
            <tr>
                <td>${common.renderDescription(item.note.html)}</td>
            </tr>
          </table>
        </td>
        </tr>
    % endif
    % if item.getSubContributionList():
        % for subcont in item.getSubContributionList():
             <%include file="SubContribution.tpl" args="item=subcont, minutes=minutes"/>
        % endfor
    % endif
    </table>
  </td>
</tr>
