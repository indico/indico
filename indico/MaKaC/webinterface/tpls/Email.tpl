<form action=${ postURL } method="POST">

    <table width="80%" align="center" border="0" style="border-left: 1px solid #777777">
        <tr>
            <td colspan="2" class="groupTitle">${ _("Send Email")}</td>
        </tr>
        <tr>
            <td>To: </td>
              <td>
              <%listUsers=[]%>
                  % for user in toUsers:
                      <input type="hidden" name="to" value="${user.getId()}"></input>
                      <% listUsers.append(user.getFirstName() + " " +  user.getFamilyName()) %>
                  % endfor
                  ${";".join(listUsers)}
              </td>
        </tr>
        <tr>
            <td>From: </td>
          <td><input type="hidden" name="from" value="${fromUser.getId()}"></input>${fromUser.getFirstName() + " " +  fromUser.getFamilyName()}</td>
        </tr>
           <tr>
            <td>Subject:</td>
            <td><input type="text" name="subject" size="50" value="${ subject }"></text></td>
        </tr>
           <tr>
            <td valign="top">Body:</td>
            <td><textarea name="body" rows="15" cols="85">${ body }</textarea></td>
        </tr>
        <tr>
            <td colspan="2" align="center">
                <input type="submit" class="btn" name="OK" value="${ _("send")}">
                <input type="submit" class="btn" name="cancel" value="${ _("cancel")}">
            </td>
        </tr>
    </table>
</form>
