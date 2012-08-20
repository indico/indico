<script type="text/javascript">
    include(ScriptRoot + "indico/Timetable/Loader.js");
</script>

<div class="groupTitle">${ _("Details for") } <b>${ fullName }</b></div>
<table >
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Email")}</span></td>
        % if self_._aw.getUser():
            <td bgcolor="white" width="100%" valign="top" class="blacktext">&nbsp;&nbsp;&nbsp;<a href="mailto:${ email }">${ email }</a></td>
        % else:
            <td bgcolor="white" width="100%" valign="top" class="blacktext">&nbsp;&nbsp;&nbsp;<span style="color: #888">${ _("Login to see the email")}</span></td>
        % endif
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Affiliation")}</span></td>
        <td bgcolor="white" width="100%" valign="top" class="blacktext">&nbsp;&nbsp;&nbsp;${ affiliation }</td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Address")}</span></td>
        <td bgcolor="white" width="100%" valign="top" class="blacktext"><pre>&nbsp;&nbsp;${ address }</pre></td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Telephone")}</span></td>
        <td bgcolor="white" width="100%" valign="top" class="blacktext">&nbsp;&nbsp;&nbsp;${ telephone }</td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Fax")}</span></td>
        <td bgcolor="white" width="100%" valign="top" class="blacktext">&nbsp;&nbsp;&nbsp;${ fax }</td>
    </tr>
</table>

<div class="groupTitle">${ _("Author in the following contribution(s)")}</div>
<div>
    % for i, contrib in enumerate(contributions):
        <div class="contribItem" style="clear: both; padding-bottom: 7px; padding-left: 20px;">
            <a href="${contrib['url']}">${contrib['title']}</a>
            % if contrib['materials']:
                <img id="materialMenuIcon${i}" title="${_('materials')}" src="./images/material_folder.png" width=12 height=12 style="cursor: pointer;"/>
                <script type="text/javascript">
                $("#materialMenuIcon${i}").click(function() {
                    var timetable = new TimetableBlockBase();
                    timetable.createMaterialMenuQtip($(this), ${contrib['materials']});
                    $(this).qtip().show();
                });
                </script>
            % endif
        </div>
    % endfor
</div>