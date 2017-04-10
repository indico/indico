<div class="conferenceDetails">
  <div itemprop="description" class="description ${'nohtml' if not description_html else ''}">${description}</div>

  <div class="infogrid">
  <div class="infoline date">
      <span  title="${_("Date/Time")}" class="icon icon-time" aria-hidden="true"></span>
      <div class="text">
        <div class="date_start">
            ${_('<span class="label">Starts</span> <span class="datetime">{0} {1}</span>').format(dateInterval[0], dateInterval[1])}
        </div>
        <div class="date_end">
            ${_('<span class="label">Ends</span> <span class="datetime">{0} {1}</span>').format(dateInterval[2], dateInterval[3])}
        </div>
        <div class="timezone">${timezone}</div>
      </div>
  </div>

  % if event.has_location_info or event.address:
    <div class="infoline location">
        <span title="${_("Location")}" class="icon icon-location" aria-hidden="true"></span>
        <div class="place text">
          ${event.venue_name}
        </div>
      % if event.room and event.room.map_url:
        <div class="room text">
          <a href="${event.room.map_url}">${event.room_name}</a>
        </div>
      % elif event.room_name:
        <div class="room text">
          ${event.room_name}
        </div>
      % endif
      % if event.address:
        <div class="address text nohtml">${event.address}</div>
      % endif
    </div>
  % endif

  % if event.person_links:
  <div class="infoline chairs clear">
      <span  title="${_("Chairpersons")}" class="icon icon-user-chairperson" aria-hidden="true"></span>
      <ul class="chair_list text">
        % for link in sorted(event.person_links, key=lambda l: l.display_order_key):
        <li>
          % if link.email:
            % if _session.user:
              <a href="mailto:${link.email}">${link.full_name}</a>
            % else:
              <a href="#" class="nomail">${link.full_name}</a>
            % endif
          % else:
            ${link.full_name}
          % endif
        </li>
        % endfor
      </ul>
  </div>
  % endif
  % if isSubmitter or conf.as_event.attached_items:
  <div class="infoline material material-list">
      ${ render_template('attachments/mako_compat/attachments_tree.html', event=conf.as_event, can_edit=isSubmitter) }
  </div>
  % endif

  % if moreInfo:
  <div class="infoline info">
      <span  title="${_("Extra information")}" class="icon icon-info" aria-hidden="true"></span>
      <div class="text ${'nohtml' if not moreInfo_html else ''}">${ moreInfo }</div>
  </div>
  % endif
  </div>
  ${ template_hook('conference-home-info', event=conf.as_event) }
</div>

${ actions }


<script type="text/javascript">
    $('.chair_list .nomail').qtip({
        content: {
            text: $T("Login to see email address"),
        },
    });
    setupAttachmentTreeView();
</script>
