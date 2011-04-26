    <tr>
    <td class="titleCellFormat" style="border-bottom: 1px solid #888; padding-right:10px" colspan="2">
        ${ form.getTitle() }
        <img src= "${ Config.getInstance().getSystemIconURL("checkAll")}"  border="0" alt="Select all" onclick="javascript:selectOneStatus('${ htmlFormName }')">
        <img src= "${ Config.getInstance().getSystemIconURL("uncheckAll")}"  border="0" alt="Select all" onclick="javascript:unselectOneStatus('${ htmlFormName }')"></span><br>
    </td>
    </tr>

    <% checked="" %>
    % if filterCrit.getField(critFormName).getShowNoValue():
       <%  checked=" checked" %>
    % endif
    <tr><td align="left" valign="top"><input type="checkbox" name="${ htmlFormName + "ShowNoValue" }" ${ checked } value= "--none--" ></td><td width="100%" align="left" valign="top"> ${ _("--not set--")}</td></tr>
    % for itemId in form:
       <% checked="" %>
       % if form[itemId].getId() in filterCrit.getField(critFormName).getValues():
          <%  checked=" checked" %>
       % endif
       <tr><td align="left" valign="top"><input type="checkbox" name="${ htmlFormName }" ${ checked } value= "${ form[itemId].getId() }" ></td><td width="100%" align="left" valign="top">${ form[itemId].getCaption() }</td></tr>
    % endfor
