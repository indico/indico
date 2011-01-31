<table width="60%" class="gestiontable" >
  <tbody>
    <tr>
      <td NOWRAP>
        Minimal horizontal margin (cm)
      </td>
      <td>
        <input name="marginH" size="5" value="0">
      </td>
    </tr>
    <tr>
      <td NOWRAP>
        <%= _("Minimal vertical margin (cm)")%>
      </td>
      <td width="100%">
        <input name="marginV" size="5" value="0">
      </td>
    </tr>
    <tr>
      <td NOWRAP>
        <%= _("Page size")%>
      </td>
      <td>
        <select name="pagesize">
          <%= pagesizes %>
        </select>
      </td>
    </tr>
  </tbody>
</table>