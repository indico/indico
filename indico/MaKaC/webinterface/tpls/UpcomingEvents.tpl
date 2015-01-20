<ul id="upcoming-event-list" class="main-page-list">
    % for (status, dateTime, eventTitle, eventId) in upcomingEvents:
    <li>
      <a class="title" title="${ escape(eventTitle) }" href="${ urlHandlers.UHConferenceDisplay.getURL(confId=eventId) }">${ escape(eventTitle) }</a>

      % if status == 'ongoing':
        <span class="timing">${ _("ongoing till") }&nbsp;${ self_.formatDateTime( dateTime ) }</span>
      % else:
        <span class="timing">${ _("starts") }&nbsp;${ self_.formatDateTime( dateTime ) }</span>
      % endif

    </li>
    % endfor
</ul>
