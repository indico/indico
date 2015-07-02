<%page args="item, minutes=True"/>

<%namespace name="common" file="../../${context['INCLUDE']}/Common.tpl"/>

<tr>
    <td align="left">
    <ul>
    <li>
    % if item.attached_items:
      <span class="material-list">
          ${ render_template('attachments/mako_compat/materials.html', item=item) }
      </span>
    % endif
    <span class="headline" style="font-size:x-small;">${item.getTitle()}</span>
    % if item.getDuration():
         <span class="itemDuration">(${prettyDuration(item.getDuration())})</span>
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
    % if item.getDescription():
        <br/><span class="headerInfo">${common.renderDescription(item.getDescription())}</span>
    % endif
    % if minutes and item.note:
        <br/>
          <table border="1" bgcolor="white" cellpadding="2" align="center">
            <tr>
              <td align="center" style:"font-weight:bold;">${_("Minutes")}</td>
            </tr>
            <tr>
                <td><span class="minutes">${ item.note.html }</span></td>
            </tr>
          </table>
    % endif
    </li>
    </ul>
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
        <div style="float:right">
            <%include file="../../${INCLUDE}/ManageButton.tpl" args="item=item, alignRight=True, minutesToggle=False"/>
        </div>
    </td>

</tr>
