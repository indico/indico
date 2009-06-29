
  <table class="groupTable" cellpadding="0">
    <tbody>
      <tr>
        <td colspan="1" class="subgroupTitle"> <%= _("Poster Default Templates")%></td>
      </tr>
      <tr>
        <td class="groupTitle">
           <%= _("List of default templates")%>
        </td>
      </tr>
      
      <tr>
        <td>
          <input name="New Template Button" class="btn" value="<%= _("New")%>" type="button" onClick="location.href='%(NewDefaultTemplateURL)s'">
        </td>
      </tr>

      <tr>
        <td>
          <table class="gestiontable" width="50%%">
            <tbody>
%(templateList)s
          </table>
        </td>
      </tr>
      
    </tbody>
  </table>
