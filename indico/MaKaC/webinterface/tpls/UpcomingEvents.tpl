<ul class="items">
% for (status, dateTime, eventTitle, eventId) in upcomingEvents:
<li>

  <a class="title" title="${ escape(eventTitle) }" href="${ urlHandlers.UHConferenceDisplay.getURL(confId=eventId) }">${ escape(eventTitle) }</a>

  % if status == 'ongoing':
    <em>${ _("ongoing till") }&nbsp;${ self_.formatDateTime( dateTime ) }</em>
  % else:
    <em>${ _("starts") }&nbsp;${ self_.formatDateTime( dateTime ) }</em>
  % endif

</li>
% endfor
</ul>
