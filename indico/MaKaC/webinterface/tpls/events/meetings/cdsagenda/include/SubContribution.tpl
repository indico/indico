<%page args="item, minutes=True"/>

<%namespace name="common" file="${context['INCLUDE']}/Common.tpl"/>

<tr>
    <td align="left">
    <ul>
    <li>
    <span class="headline" style="font-size:x-small;">${item.getTitle()}</span>
    % if formatDuration(item.getDuration()) != '00:00':
         <span class="itemDuration">(${prettyDuration(formatDuration(item.getDuration()))})</span>
    % endif
    % if len(item.getReportNumberHolder().listReportNumbers()) != 0:
        (
        % for rn in item.getReportNumberHolder().listReportNumbers():
                ${rn[1]}&nbsp;
        % endfor
        )
    % endif
    % if len(item.getAllMaterialList()) > 0:
        % for material in item.getAllMaterialList():
            % if material.canView(accessWrapper):
            <%include file="${INCLUDE}/Material.tpl" args="material=material, contribId=item.getId()"/>
            &nbsp;
            % endif
        % endfor
    % endif
    % if item.getDescription():
        <br/><span class="headerInfo">${common.renderDescription(item.getDescription())}</span>
    % endif
    % if minutes:
        % for minutesText in extractMinutes(item.getAllMaterialList()):
        <br/>
          <table border="1" bgcolor="white" cellpadding="2" align="center">
            <tr>
              <td align="center"><b>Minutes</b></td>
            </tr>
            <tr>
                <td><span class="minutes">${minutesText}</span></td>
            </tr>
          </table>
        % endfor
    % endif
    </li>
    </ul>
    </td>
    <td align="right">
        % if item.getSpeakerList() or item.getSpeakerText():
           ${common.renderUsers(item.getSpeakerList(), unformatted=item.getSpeakerText(), title=False, italicAffilation=false, separator=' ')}
        % endif
    </td>
    <td>
        <%include file="${INCLUDE}/ManageButton.tpl" args="item=item, alignRight=True"/>
    </td>

</tr>