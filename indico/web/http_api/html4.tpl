<ul class="indico_event_list" data-ts="${ts}">
% for date, events in fossils:
<li>
  <span class="indico_event_list_day">${date.strftime("%A %B %d, %Y")}</span>
  <ul class="indico_day_content">
    % for event in events:
    <li class="indico_event_entry" data-id="${event['id']}">
      <span class="indico_event_time">${event['startDate'].time().strftime("%H:%M")}</span>
      <span class="indico_event_category">${event['category']}</span>
      <a href="${event['url']}" title="${event['title']}">
        <span class="indico_event_tile">
          ${event['title']}
        </span>
      </a>
      <span class="indico_event_room">${event['room'] if event['room'] else ''}</span>
    </li>
    % endfor
  </ul>
</li>
% endfor
</ul>

