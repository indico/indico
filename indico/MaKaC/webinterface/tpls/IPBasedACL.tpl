<span>${_("IPs with full access to any private and public event, session, contribution, material or file")}:</span>
% if len(ipList) == 0:
  <em>None - you can add one using the form below</em>
% else:
  <ul style="display: block; width: 150px;">
    % for ip in ipList:
      <li style="display: block; height:20px;">
    <div style="float: left;">${ ip }</div>
       <form action="${ urlHandlers.UHIPBasedACLFullAccessRevoke.getURL() }" method="POST" style="display:inline;">
         <input type="image" class="UIRowButton" onclick="this.form.submit();return false;" title="Remove this IP from the list" src="${ systemIcon("remove") }" style="float: right;"/>
         <input type="hidden" name="ipAddress" value="${ ip }" />
       </form>
      </li>
    % endfor
  </ul>
% endif
<div style="margin-top: 20px;">
<form action="${ urlHandlers.UHIPBasedACLFullAccessGrant.getURL() }" method="POST">
<input type="text" name="ipAddress" style="margin-left:40px" />
<input type="Submit" value="Add"/>
</form>
</div>
