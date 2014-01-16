<%include file="MarkdownMathJaxHelp.tpl"/>


<form id="ContributionDataModificationForm" method="POST" action="${ postURL }">
    <table width="60%" align="center" border="0" style="border-left: 1px solid #777777" id="abstract-field-table">
        <tr>
            <td class="groupTitle" colspan="2"> ${ _("Edit contribution data")}</td>
        </tr>
        <tr>
            <td class="titleCellTD">
                <span class="titleCellFormat">${ _("Title")}</span><span class="mandatoryField"> *</span>
            </td>
            <td bgcolor="white" width="100%" valign="top" class="blacktext">
                <input type="text" name="title" id="title" size="80" value=${ title } />
            </td>
        </tr>
        % if self_._rh._target.getConference().getAbstractMgr().isActive() and self_._rh._target.getConference().hasEnabledSection("cfa") and self_._rh._target.getConference().getAbstractMgr().hasAnyEnabledAbstractField():
            % for field in additionalFields:
                <%include file="AbstractField.tpl" args="field=field, fdict=fieldDict"/>
            % endfor
        % else:
        <tr>
            <td class="titleCellTD">
                <span class="titleCellFormat">${ _("Description")}</span>
            </td>
            <td bgcolor="white" width="100%" valign="top" class="blacktext">
                <textarea name="description" cols="80" rows="6" wrap="soft">${ description }</textarea>
            </td>

        </tr>
        % endif
    % if sessionType != 'poster':
    <tr>
      <td style="text-align: right;">
        <span class="titleCellFormat">${ _("Date/Time")}</span>
      </td>
      <td><span id="dateTime"></span></td>
    </tr>
    <tr>
      <td style="text-align: right;">
        <span class="titleCellFormat">${ _("Duration")}</span>
      </td>
      <td><span id="duration"></span></td>
    </tr>
    % endif

    <%include file="EventLocationInfo.tpl" args="event=self_._rh._target, modifying=True, parentRoomInfo=roomInfo(self_._rh._target, level='inherited'), showParent=True, conf = self_._conf, eventId = self_.getContribId(), parentName=_('session') if contrib.getSession() else _('event')"/>


    ${ Board }
    ${ Type }
        <tr>
          <td class="titleCellTD">
            <span class="titleCellFormat">${ _("Keywords")}<br><small>( ${ _("one per line")})</small></span>
          </td>
          <td bgcolor="white" width="100%" valign="top" class="blacktext">
            <textarea name="keywords" cols="60" rows="6">${ keywords }</textarea>
          </td>
        </tr>
        <tr align="center">
          <td colspan="2" class="buttonBar" valign="bottom" align="center">
        <input type="submit" class="btn" value="${ _("ok")}" name="ok" id="ok" />
        <input type="submit" class="btn" value="${ _("cancel")}" name="cancel" />
          </td>
        </tr>
    </table>
</form>

<script type="text/javascript">
    var parameterManager = new IndicoUtil.parameterManager();
    parameterManager.add($E('title'), 'text', false);

    $("#ok").click(function() {
        if (!parameterManager.check())
            event.preventDefault();
    });
IndicoUI.executeOnLoad(function()
        {
            var info = new WatchObject();

% if contrib.isScheduled():
    % if sessionType != 'poster':
        var dateTime = IndicoUI.Widgets.Generic.dateField(true, {name: 'dateTime'});
        dateTime.set('${ dateTime }');
        dateTime.observeChange(function() {
            info.set('startDate', dateTime.get());
        });
        $E('dateTime').set(dateTime)
        info.set('startDate', dateTime.get());
    % endif
% else:
$E('dateTime').set('Not scheduled')
% endif
% if sessionType != 'poster':
    var duration = IndicoUI.Widgets.Generic.durationField('${ duration }', {name: 'duration'});
    $E('duration').set(duration);
    $E('duration').observeChange(function() {
                info.set('duration', duration.get());
            });
    info.set('duration', duration.get());
% endif

rbWidget.setDateTimeInfo(info);

            injectValuesInForm($E('ContributionDataModificationForm'));
        });


// Pagedown editor stuff

function block_handler(text, rbg) {
    return text.replace(/^ {0,3}""" *\n((?:.*?\n)+?) {0,3}""" *$/gm, function (whole, inner) {
        return "<blockquote>" + rbg(inner) + "</blockquote>\n";
    });
}

</script>
