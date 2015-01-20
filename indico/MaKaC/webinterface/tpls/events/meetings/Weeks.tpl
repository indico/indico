<%namespace name="common" file="${context['INCLUDE']}/Common.tpl"/>

<%
    from collections import defaultdict, OrderedDict
    from itertools import takewhile
    _firstDay = (parseDate(firstDay, format="%d-%B-%Y") if firstDay else startDate).date()
    _lastDay = (parseDate(lastDay, format="%d-%B-%Y") if lastDay else endDate).date()

    firstWeekday = _request.args.get('firstWeekday', 'monday')  # monday/sunday/event
    sundayFirst = (firstWeekday == 'sunday')
    showEndTimes = _request.args.get('showEndTimes') == '1'


    def _processEntry(entry):
        """Flatten the timetable into single entries"""
        itemType = getItemType(entry)
        startTime = entry.getAdjustedStartDate(timezone)
        if itemType == 'Contribution':
            yield 'contrib', startTime, entry
        elif itemType == 'Break':
            yield 'break', startTime, entry
        elif itemType == 'Session':
            for subEntry in entry.getSchedule().getEntries():
                if subEntry.__class__.__name__ != 'BreakTimeSchEntry':
                    subEntry = subEntry.getOwner()
                    if not subEntry.canView(accessWrapper):
                        continue
                for tmp in _processEntry(subEntry):
                    yield tmp


    def buildTable():
        allEntries = defaultdict(list)
        for entry in entries:
            entryDate = entry.getAdjustedStartDate(timezone).date()
            if _firstDay <= entryDate <= _lastDay:
                allEntries[entryDate] += _processEntry(entry)

        if not allEntries:
            return [], False

        hasWeekends = any(x.weekday() in (5, 6) for x in allEntries)

        sortedDates = sorted(allEntries.iterkeys())
        firstShownDay = sortedDates[0]
        lastShownDay = sortedDates[-1]
        if firstWeekday != 'event':
            weekStart = 6 if sundayFirst else 0
            if firstShownDay.weekday() != weekStart:
                firstShownDay -= timedelta(days=firstShownDay.weekday()) + timedelta(days=int(hasWeekends and sundayFirst))

        weekTableShallow = []
        skippedDays = 0
        for i, offset in enumerate(xrange((lastShownDay - firstShownDay).days + 1)):
            day = firstShownDay + timedelta(days=offset+skippedDays)
            if day > lastShownDay:
                # the loop doesn't account for skipped days so we might have to break early
                break
            if not hasWeekends and day.weekday() == 5:
                day += timedelta(days=2)
                skippedDays += 2
            if i % (7 if hasWeekends else 5) == 0:
                weekTableShallow.append([])
            weekTableShallow[-1].append((day, allEntries[day]))

        # build a new week table that contains placeholders
        weekTable = []
        for week in weekTableShallow:
            # Build list of time slots that are used this week
            slots = set()
            for day, dayEntries in week:
                slots.update(getTime(x[1]) for x in dayEntries)

            # Build each day with its contributions and placeholders
            tmp = []
            for day, dayEntries in week:
                dayTmp = defaultdict(list)
                for row in dayEntries:
                    startTime = row[1]
                    dayTmp[getTime(startTime)].append((row[0], row[2]))
                for slot in sorted(slots):
                    dayTmp.setdefault(slot, None)
                tmp.append((day, OrderedDict(sorted(dayTmp.items()))))

            weekTable.append(tmp)
        return weekTable, hasWeekends

    weekTable, hasWeekends = buildTable()
%>

<div class="event-info-header">
    <div>
        <div class="event-title">${conf.getTitle()}</div>
        ${common.renderEventTimeCompact(startDate, endDate)}
    </div>
</div>

<div class="week-timetable-wrapper">
    % for week in weekTable:
        <div class="clearfix week-timetable ${'no-weekends' if not hasWeekends else ''}">
            <ul>
                % for j, (day, dayEntries) in enumerate(week):
                    % if j > 0:
                        <li class="spacer"></li>
                    % endif
                    <li>
                        <div class="row day-header">${prettyDate(day)}</div>
                        <%
                            dayEntriesItems = dayEntries.items()
                            hidePlaceholders = 0
                        %>
                        % for n, (startTime, slotEntries) in enumerate(dayEntriesItems):
                            % if slotEntries is None:
                                <%
                                    if hidePlaceholders:
                                        hidePlaceholders -= 1
                                        continue
                                %>
                                <div class="row placeholder ${'occupied' if lastEndTime and startTime < lastEndTime else ''}" data-slot="${startTime}"></div>
                            % else:
                                % for i, (entryType, entry) in enumerate(slotEntries):
                                    <%
                                        endTime = getTime(entry.getAdjustedEndDate(timezone))
                                        height = 18
                                        if i == 0:
                                            adjacentPlaceholders = takewhile(lambda x: x[1] is None, iter(dayEntriesItems[n+1:]))
                                            hidePlaceholders = sum(1 for x in adjacentPlaceholders if x[1] is None and x[0] < endTime)
                                            height += (height + 1) * hidePlaceholders
                                        extraStyles = ['height: {0}px'.format(height)]
                                        if i > 0:
                                            extraStyles.append('display: none')
                                        if entryType == 'contrib' and entry.getSession():
                                            sessionName = entry.getSession().getTitle()
                                            sessionColor = entry.getSession().getColor()
                                        hasSession = entryType == 'contrib' and entry.getSession()
                                        hasMulti = len(slotEntries) > 1 and i == 0
                                        classes = ['row', entryType]
                                        if i > 0:
                                            classes.append('js-same-time')
                                        if hasSession:
                                            classes.append('has-session')
                                        if hasMulti:
                                            classes.append('has-multi')
                                    %>
                                    <div class="${' '.join(classes)}" style="${'; '.join(extraStyles)}" data-slot="${startTime}">
                                        <span class="time">
                                            ${startTime if i == 0 else ''}
                                            % if hidePlaceholders and showEndTimes:
                                                <span class="end-time">${endTime}</span>
                                            % endif
                                        </span>
                                        % if entryType == 'contrib':
                                            <a class="week-anchor" href="${url_for('event.contributionDisplay', confId=conf.getId(), contribId=entry.getId())}">
                                        % endif
                                        <span class="main">
                                            <span class="title">${entry.getTitle()}</span>
                                            % if entryType == 'contrib':
                                                % if entry.getSpeakerList() or entry.getSpeakerText():
                                                    - ${common.renderUsers(entry.getSpeakerList(), unformatted=entry.getSpeakerText(), title=False, spanClass='compact-speakers', italicAffilation=False, separator=' ')}
                                                % endif
                                            % endif
                                        </span>
                                        % if entryType == 'contrib':
                                            </a>
                                        % endif
                                        <div class="tooltip hidden">
                                            <strong>${entry.getTitle()}</strong><br>
                                            % if entryType == 'contrib' and (entry.getSpeakerList() or entry.getSpeakerText()):
                                                 ${common.renderUsers(entry.getSpeakerList(), unformatted=entry.getSpeakerText(), title=False, spanClass='compact-speakers', italicAffilation=False, separator=' ')}<br>
                                            % endif
                                            ${startTime} - ${endTime}<br>
                                            % if entry.getRoom() and entry.getRoom().getName():
                                                Room: ${entry.getRoom().getName()}<br>
                                            % endif
                                            % if hasSession:
                                                Session: ${sessionName}<br>
                                            % endif
                                        </div>
                                        % if hasSession:
                                            <i class="icon-circle-small session-mark" title="Session: ${sessionName}" data-qtip-opts='{"show":{"solo":true}, "style":{"classes":"informational"}}' style="color: ${sessionColor};"></i>
                                        % endif
                                        % if hasMulti:
                                            <i class="icon-expand more-contribs" title="There are ${len(slotEntries)-1} more contributions at this time. Click this icon to show them." data-qtip-opts='{"show":{"solo":true}, "style":{"classes":"informational"}}'></i>
                                        % endif
                                    </div>
                                % endfor
                            % endif
                        % endfor
                    </li>
                % endfor
            </ul>
        </div>
    % endfor
</div>

<script>
    $('.more-contribs').css('cursor', 'pointer').on('click', function() {
        var row = $(this).closest('.row');
        var additional = row.nextUntil(':not(.js-same-time)');
        additional.toggle();
        $(this).toggleClass('icon-expand icon-collapse');
        if (additional.is(':visible')) {
            $('.more-contribs').not(this).filter(function() {
                return !!$(this).closest('.row').next('.js-same-time:visible').length;
            }).trigger('click');
        }
        var sameSlotHeight = row.height() * (additional.filter(':visible').length + 1);
        row.closest('li').siblings('li').find('.row').filter(function() {
            return $(this).data('slot') == row.data('slot');
        }).height(sameSlotHeight);
    });

    $('.week-timetable .row:has(.tooltip)').qtip({
        content: {
            text: function() {
                return $('.tooltip', this).html();
            }
        },
        show: {
            solo: true
        },
        position: {
            my: 'center right',
            at: 'center left'
        },
        style: {
            classes: 'informational'
        }
    });
</script>
