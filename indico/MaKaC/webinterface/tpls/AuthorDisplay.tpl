<div class="groupTitle">${ _("Details for") } <b>${ fullName }</b></div>
<table>
  % if self_._aw.getUser():
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Email")}</span></td>
        <td bgcolor="white" width="100%" valign="top" class="blacktext"><a href="mailto:${ email }">${ email }</a></td>
    </tr>
  % endif
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Affiliation")}</span></td>
        <td bgcolor="white" width="100%" valign="top" class="blacktext">${ affiliation }</td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Address")}</span></td>
        <td bgcolor="white" width="100%" valign="top" class="blacktext"><pre>${ address }</pre></td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Telephone")}</span></td>
        <td bgcolor="white" width="100%" valign="top" class="blacktext">${ telephone }</td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Fax")}</span></td>
        <td bgcolor="white" width="100%" valign="top" class="blacktext"> ${ fax }</td>
    </tr>
</table>

<div class="groupTitle">${ _("Author in the following contribution(s)")}</div>
<div>
    % for i, contrib in enumerate(contributions):
        <div class="contribItem" style="clear: both; padding-bottom: 7px; padding-left: 20px;">
            <a href="${contrib['url']}">${contrib['title']}</a>
            % if contrib['materials']:
                <img class="material_icon" title="${_('materials')}" src="${Config.getInstance().getImagesBaseURL()}/material_folder.png" width=12 height=12 style="cursor: pointer;"/>
                <%include file="MaterialListPopup.tpl" args="materials=contrib['materials']"/>
            % endif
        </div>
    % endfor
</div>
