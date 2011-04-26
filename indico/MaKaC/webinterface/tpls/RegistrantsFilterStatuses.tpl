<table width="100%" cellpadding="0" cellspacing="0" valign="top">
    <% counter=0 %>
    % for key in statuses:
        <% statusName = statusObjects[key].getCaption() %>
        % if counter == 0:
            <tr>
        % endif
        <td style="border-bottom:1px solid lightgrey; width:33%" valign="top" id="${ key }" align="left"><span style="color:black">
            <b>${ statusName }</b>
            <img src= "${ Config.getInstance().getSystemIconURL("checkAll")}"  border="0" alt="Select all" onclick="javascript:selectOneStatus('${ key }')">
            <img src= "${ Config.getInstance().getSystemIconURL("uncheckAll")}"  border="0" alt="Select all" onclick="javascript:unselectOneStatus('${ key }')"></span><br>

        <% checked="" %>
        <% valueToCheck = statusName + key + "-NoValue" %>
        % if valueToCheck in self_._filterCrit.getField("statuses").getValues():
            <%  checked=" checked" %>
        % endif
        <table width="100%" cellpadding="0" cellspacing="0" valign="top">
            <tr><td align="left" valign="top"><input type="checkbox" name="statuses" ${ checked } value= "${ statusName+key}-NoValue" ></td><td width="100%" align="left" valign="top"> ${ _("--not set--")}</td></tr>
        </table>
        % for value in statuses[key]:
            <% checked="" %>
            <% valueToCheck = statusName + key + "-" + statuses[key][value].getCaption() %>
            % if valueToCheck in self_._filterCrit.getField("statuses").getValues():
               <%  checked=" checked" %>
            % endif
            <table width="100%" cellpadding="0" cellspacing="0" valign="top">
                <tr><td align="left" valign="top"><input type="checkbox" name="statuses" ${ checked } value= "${ statusName+key }-${ statuses[key][value].getCaption()}" ></td><td width="100%" align="left" valign="top">${ statuses[key][value].getCaption() }</td></tr>
            </table>
        % endfor
        </td>
        % if counter == 2:
            <% counter=0 %>
            </tr>
        % else:
            <% counter+=1 %>
        % endif
    % endfor
    % if counter in [1,2]:
        <td colspan="2" style="border-bottom:1px solid lightgrey; width:100%">&nbsp;</td>
    % endif
</table>
