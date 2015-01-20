
<form action="${ removeIdentityURL }" method="POST" style="margin: 0;">
<table>
% for item in identityItems:
<tr>
  <td width="60%">
    % if accountManagementActive:
    <input type="checkbox" name="selIdentities" value="${ item.getId() }" />
    % endif
    ${ item.getLogin() }
  </td>
  <td width="20%">
    ${ item.getAuthenticatorTag() }
  </td>
  <td>
    % if item.getAuthenticatorTag() == "Local":
    <a href="${ urlHandlers.UHUserIdentityChangePassword.getURL(userId=avatar.getId(), login=item.getId()) }">
      <small> ${ _("Change password") }</small>
    </a>
    % else:
    External account
    % endif
  </td>
</td>
</tr>
% endfor
    <tr>
        <td>
        <table>
            <tr>
                % if accountManagementActive:
                <td>
                    <input type="submit" class="btn" value="${ _("delete selected accounts")}" name="action">
                    </form>
                </td>
                <td>
                <form style="margin: 0; padding: 0;" action="${ addIdentityURL }" method="POST">
                    <input type="submit" class="btn" value="${ _("create a new account")}" name="action">
                </form>
                </td>
                % endif
            </tr>
        </table>
        </td>
    </tr>
</table>
