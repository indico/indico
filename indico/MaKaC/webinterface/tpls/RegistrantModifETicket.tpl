<table border="0">
  <tr>
    <td>
      <a href="${ eTicketUrl }">
        <i class="icon-file-pdf"></i>
        ${ _("Download registrant's ticket") }
      </a>
    </td>
  </tr>
  <tr>
    <td>
      <table border="0">
        <tr>
          <td>
            <span class="dataCaptionFormat"><b>${ _("Checked in:") }<b/></span>
          </td>
          % if isCheckedIn:
          <td><span class="successText">${ _("Yes") }</span></td>
          % else:
          <td><span class="warningText">${ _("No") }</span></td>
          <td>
          <form action="" method="POST">
              <div>
                <input name="changeTo" type="hidden" value="True">
                <small><input type="submit" class="btn" value="Check in"></small>
              </div>
          </form>
          </td>
          % endif
        </tr>
        % if isCheckedIn:
        <tr>
          <td>
            <span class="dataCaptionFormat"><b>${ _("Check in date:") }<b/></span>
          </td>
          <td>${ checkInDate }</td>
        </tr>
        % endif
      </table>
    </td>
  </tr>
</table>
