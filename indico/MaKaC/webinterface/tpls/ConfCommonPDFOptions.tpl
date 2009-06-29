<table width="100%%">
  <tbody>
    <tr>
      <td class="groupTitle" colspan="2">
        <span> <%= _("PDF Options")%> </span>
      </td>
    </tr>
    <tr>
      <td class="titleCellTD" NOWRAP>
         <%= _("Page size")%>
      </td>
      <td width="100%%">
        <select name="pagesize">
          %(pagesizes)s
        </select>
      </td>
    </tr>
    <tr>
      <td class="titleCellTD" NOWRAP>
         <%= _("Font size")%>
      </td>
      <td width="100%%">
        <select name="fontsize">
          %(fontsizes)s
        </select>
      </td>
    </tr>
    <tr>
      <td class="titleCellTD" NOWRAP>
         <%= _("Begin page numbers with number")%>
      </td>
      <td width="100%%">
        <input name="firstPageNumber" value="1">
      </td>
    </tr>
  </tbody>
</table>

