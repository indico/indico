<form action='<%= NewTemplateURL %>' method='post'>
  <table class="groupTable" cellpadding="0">
    <tbody>
      <tr>
        <td colspan="2" class="subgroupTitle"> <%= _("Badge Printing")%></td>
      </tr>

      <tr>
        <td  colspan="2">
          &nbsp;
        </td>
      </tr>
      <tr>
        <td  colspan="2" class="groupTitle">
	        <%= _("Create a new template")%>
        </td>
      </tr>
      <tr>
      	<td class="titleCellTD" NOWRAP>
        	 <%= _("Based on")%>:
      	</td>
      	<td>
        	<select name="baseTemplate">
          	<%= baseTemplates %>
        	</select>
      	</td>

    </tr>
     <tr>
     	<td></td>
        <td>
          <input name="New Template Button" class="btn" value="<%= _("New")%>" type="submit">
        </td>
     </tr>

</form>
<form action='<%= CreatePDFURL %>' method='post' target='_blank'>

      <tr>
        <td colspan="2" class="groupTitle">
	        <%= _("List of available templates")%>
        </td>
      </tr>

      <tr>
        <td colspan="2">
          <table class="gestiontable" width="50%">
            <tbody>
<%= templateList %>
          </table>
        </td>
      </tr>

      <tr>
        <td>
          <input class="btn" value="<%= _("Try Selected Template")%>" type="submit" <%= TryTemplateDisabled %>>
        </td>
      </tr>

    </tbody>
  </table>

  <table width="100%" class="gestiontable" >
    <tbody>
      <tr>
        <td class="groupTitle">
          <span><%= _("PDF Options")%></span>
        </td>
      </tr>
      <%= PDFOptions %>
    </tbody>
  </table>
</form>
