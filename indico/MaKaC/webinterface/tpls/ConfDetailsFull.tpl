<span itemprop="description">${ description }</span>
<table class="conferenceDetails">
  <tr>
    <td colspan="2"><br></td>
  </tr>
  <tr>
    <td align="right" valign="top" class="displayField"><b> ${ _("Dates")}:</b></td>
    <td>${ dateInterval }</td>
  </tr>
  <tr>
    <td align="right" valign="top" class="displayField"><b> ${ _("Timezone")}:</b></td>
    <td>${ timezone }</td>
  </tr>
  <tr>
    <td align="right" valign="top" class="displayField"><b> ${ _("Location")}:</b></td>
    <td>${ location }</td>
  </tr>

  <tr>
    <td align="right" valign="top" class="displayField"><strong>${_("Chairs:")}</strong></td>
    <td>
      <ul class="chair_list">
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
    </td>
  </tr>

  ${ material }
  ${ moreInfo }

</table>
${ actions }

<script type="text/javascript">
      $('.chair_list .nomail').qtip({
             content: {
                 text: $T("Login to see email address"),
             },
         });
</script>
