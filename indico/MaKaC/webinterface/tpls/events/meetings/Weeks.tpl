<%namespace name="common" file="${context['INCLUDE']}/Common.tpl"/>

<%
    from collections import defaultdict, OrderedDict
    _firstDay = (parseDate(firstDay, format="%d-%B-%Y") if firstDay else startDate).date()
    _lastDay = (parseDate(lastDay, format="%d-%B-%Y") if lastDay else endDate).date()

    firstWeekday = _request.args.get('firstWeekday', 'monday')  # monday/sunday/event
    sundayFirst = (firstWeekday == 'sunday')


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
                        % for startTime, slotEntries in dayEntries.iteritems():
                            % if slotEntries is None:
                                <div class="row placeholder" data-slot="${startTime}"></div>
                            % else:
                                % for i, (entryType, entry) in enumerate(slotEntries):
                                    <%
                                        extraStyle = 'display: none; ' if i > 0 else ''
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
                                    <div class="${' '.join(classes)}" style="${extraStyle}" data-slot="${startTime}">
                                        <span class="time">${startTime if i == 0 else ''}</span>
                                        <span class="main">
                                            <span class="title">${entry.getTitle()}</span>
                                            % if entryType == 'contrib':
                                                % if entry.getSpeakerList() or entry.getSpeakerText():
                                                    - ${common.renderUsers(entry.getSpeakerList(), unformatted=entry.getSpeakerText(), title=False, spanClass='compact-speakers', italicAffilation=False, separator=' ')}
                                                % endif
                                            % endif
                                        </span>
                                        % if hasSession:
                                            <i class="icon-circle-small session-mark" title="Session: ${sessionName}" style="color: ${sessionColor};"></i>
                                        % endif
                                        % if hasMulti:
                                            <i class="icon-expand more-contribs" title="There are ${len(slotEntries)-1} more contributions at this time. Click this icon to show them."></i>
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

    $('.week-timetable').on('mouseenter', '.row .main:not([title])', function() {
        var $this = $(this);
        if(this.scrollWidth > this.offsetWidth) {
            // Setting a title will cause a qtip to be created
            $this.attr('title', $this.text());
        }
    });
</script>
