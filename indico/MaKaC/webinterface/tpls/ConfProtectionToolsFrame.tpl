<table width="100%" align="center" border="0">
<tr>
  <td colspan="5" class="groupTitle">Tools</td>
</tr>
<tr>
  <td bgcolor="white" width="80%">
    <table width="100%">
    <tr>
    <form action="${ grantSubmissionToAllSpeakersURL }" method="POST">
      <td width="50%">
        <input type="submit" class="btn" value="${ _("Grant submission rights to all speakers")}">
      </td>
    </form>
    <form action="${ removeAllSubmissionRightsURL }" method="POST">
      <td>
        <input type="submit" class="btn" value="${ _("Remove all submission rights")}">
      </td>
    </form>
    </tr>
    <tr>
    <form action="${ grantModificationToAllConvenersURL }" method="POST">
      <td>
        <input type="submit" class="btn" value="${ _("Grant modification rights to all session conveners")}">
      </td>
    </form>
      <td></td>
    </tr>
    </table>
  </td>
</tr>
</table>
