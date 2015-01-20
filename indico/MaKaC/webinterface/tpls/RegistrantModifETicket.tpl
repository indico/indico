<div>
  <div>
    <a href="${ eTicketUrl }">
    <i class="icon-file-pdf"></i>
    ${_("Download registrant's ticket")}
    </a>
  </div>
  <div>

  </div>
  <form action="${checkInUrl}" method="POST">
    <span><b>${_("Checked in:")}</b></span>
    % if isCheckedIn:
      <span class="successText">${_("Yes")}</span>
    % else:
      <span class="warningText">${_("No")}</span>
    % endif
    <input name="changeTo" type="hidden"
           value="${'False' if isCheckedIn else 'True'}">
    <input type="submit"
           value="${_('Uncheck in') if isCheckedIn else _('Checkin')}">
  </form>
  % if isCheckedIn:
    <div>
      <span><b>${ _("Check in date:") }</b></span>
      <span>${checkInDate}</span>
    </div>
  % endif
</div>
