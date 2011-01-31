
  <table class="groupTable" cellpadding="0">
    <tbody>
      <tr>
        <td colspan="1" class="subgroupTitle"><%= _("Badge Default Templates")%></td>
      </tr>
      <tr>
        <td class="groupTitle">
          <%= _("List of default templates")%>
          <% inlineContextHelp( _('Templates that will be available for all conferences.') ) %>
        </td>
      </tr>

      <tr>
        <td>
          <input name="New Template Button" class="btn" value="<%= _("New")%>" type="button" onClick="location.href='<%= NewDefaultTemplateURL %>'">
        </td>
      </tr>

      <tr>
        <td>
          <table class="gestiontable" width="50%">
            <tbody>
              <%= templateList %>
          </table>
        </td>
      </tr>

      <tr>
        <td class="groupTitle">
          <%= _("Default PDF Options")%>
          <% inlineContextHelp( _('Initial PDF options after a conference is created.') ) %>
        </td>
      </tr>
<form method="post" action="<%=urlHandlers.UHTemplatesSetDefaultPDFOptions.getURL()%>">
     <tr>
       <td>
         <input name="savePDFOptions" class="btn" value="<%= _("Save")%>" type="submit">
       </td>
     </tr>
      <%= PDFOptions %>
</form>
    </tbody>
  </table>