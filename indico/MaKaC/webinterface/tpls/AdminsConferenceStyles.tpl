  <table class="groupTable" cellpadding="0">
    <tbody>
      <tr>
        <td colspan="1" class="groupTitle">${ _("Available Styles")}
          ${inlineContextHelp(contextHelpText)}
        </td>
      </tr>
      <tr>
        <td>
          <table cellspacing="1" align="center">
          <tr style="border-bottom: 1px;"><th>${ _("Name")}</th><th>${ _("URL")}</th></tr>
          <% styles = cssTplsModule.getCssTplsList() %>
          <% styles.sort(lambda x,y: cmp(x.getFileName(), y.getFileName())) %>
          % for style in styles:
          <tr>
            <td align="left" style="padding-right: 10px"><strong>${style.getFileName()}</strong></td>
            <td align="left">${style.getURL()}</td>
          </tr>
          % endfor
          </table>
        </td>
      </tr>
    </tbody>
  </table>
