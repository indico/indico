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

  % if location:
    <div class="infoline location">
        <span title="${_("Location")}" class="icon icon-location" aria-hidden="true"></span>
        <div class="place text">
          ${location}
        </div>
      % if room:
        <div class="room text">${room}</div>
      % endif
      % if address:
        <div class="address text nohtml">${address}</div>
      % endif
    </div>
  % endif

  % if chairs:
  <div class="infoline chairs clear">
      <span  title="${_("Chairpersons")}" class="icon icon-user-chairperson" aria-hidden="true"></span>
      <ul class="chair_list text">
        % for chair in chairs:
        <li>
          % if chair.getEmail():
            % if self_._aw.getUser():
              <a href="mailto:${chair.getEmail()}">${chair.getFullName()}</a>
            % else:
              <a href="#" class="nomail">${chair.getFullName()}</a>
            % endif
          % else:
            ${chair.getFullName()}
          % endif
        </li>
        % endfor
      </ul>
  </div>
  % endif
  % if conf.attached_items or isSubmitter:
  <div class="infoline material material-list">
      ${ render_template('attachments/mako_compat/attachments_tree.html', linked_object=conf, can_edit=isSubmitter) }
  </div>
  % endif

  % if moreInfo:
  <div class="infoline info">
      <span  title="${_("Extra information")}" class="icon icon-info" aria-hidden="true"></span>
      <div class="text ${'nohtml' if not moreInfo_html else ''}">${ moreInfo }</div>
  </div>
  % endif

  ${ template_hook('conference-home-info', event=conf) }
  </div>
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
