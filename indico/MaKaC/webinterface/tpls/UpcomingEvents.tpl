<ul>
% for (status, dateTime, eventTitle, eventId) in upcomingEvents:
<li>

  <a title="${ escape(eventTitle) }" href="${ urlHandlers.UHConferenceDisplay.getURL(confId=eventId) }">${ truncateTitle(escape(eventTitle), maxSize=45) }</a>

  % if status == 'ongoing':
    <em>${ _("ongoing till") }&nbsp;${ self_.formatDateTime( dateTime ) }</em>
  % else:
    <em>${ _("starts") }&nbsp;${ self_.formatDateTime( dateTime ) }</em>
  % endif

</li>
% endfor
</ul>
