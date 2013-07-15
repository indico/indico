
    <!-- CONTEXT HELP DIVS -->
    <div id="tooltipPool" style="display: none">
        <!-- Where is key? -->
        <div id="features" class="tip">
            ${ _("""<b>Click on one item to enable/disable the option.</b><br>
            - <b>News</b>: will display "latest news" on Indico home page and menu<br>
            - <b>Debug</b>: will display extensive debug information on error pages.""")}
        </div>
    </div>
    <!-- END OF CONTEXT HELP DIVS -->


<div class="groupTitle">${ _("General System Information")}</div>

<table class="groupTable">
<tr>
  <td>
    <table width="100%" border="0">
    <tr>
      <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("System title")}</span></td>
      <td bgcolor="white" width="100%" valign="top" class="blacktext">${title}</td>
      <td rowspan="4" valign="top">
        <form action="${ GeneralInfoModifURL }" method="GET">
        <input type="submit" class="btn" value="${ _("modify")}">
        </form>
      </td>
    </tr>
    <tr>
      <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Organisation")}</span></td>
      <td bgcolor="white" width="100%" valign="top" class="blacktext">${ organisation }</td>
    </tr>
    <tr>
      <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Support email")}<br/>(${ _("for automatic messages") })</span></td>
      <td bgcolor="white" width="100%" valign="top" class="blacktext">${ supportEmail }</td>
    </tr>
    <tr>
      <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Support email")}<br/>${ _("(for public display in page footers)")}</span></td>
      <td bgcolor="white" width="100%" valign="top" class="blacktext">${publicSupportEmail}</td>
    </tr>
    <tr>
      <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("No reply email")}<br/>${ _("(for automatic messages that don't need answer)")}</span></td>
      <td bgcolor="white" width="100%" valign="top" class="blacktext">${ escape(noReplyEmail) }</td>
    </tr>
    <tr>
      <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Language")}</span></td>
      <td bgcolor="white" width="100%" valign="top" class="blacktext">${ _(lang)}</td>
    </tr>
    <tr>
       <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Timezone")}</span></td>
       <td bgcolor="white" width="100%" valign="top" class="blacktext">${ timezone }</td>
    </tr>
    <tr>
      <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Address")}</span></td>
      <td bgcolor="white" width="100%" valign="top" class="blacktext">${address}</td>
    </tr>
    <tr>
      <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Features")}</span></td>
      <td bgcolor="white" width="100%" valign="top" class="blacktext"><table><tr><td>${features}</td><td valign="top">${contextHelp('features' )}</td></tr></table></td>
    </tr>
    </table>
  </td>
</tr>
</table>

<div class="groupTitle" style="margin-top: 30px;">${ _("Administrator list")}</div>
<table width="100%">
    <tr>
        <td bgcolor="white" width="60%">
            <table width="100%">
                <tr>
                    <td><ul id="inPlaceAdministrators" class="UIPeopleList"></ul></td>
                </tr>
                <tr>
                    <td nowrap style="width:60%; padding-top:5px;">
                        <input type="button" onclick="adminListManager.addExistingUser();" value='${ _("Add administrator") }'></input>
                    </td>
                    <td></td>
                </tr>
            </table>
        </td>
    </tr>
</table>

<script>

var adminListManager = new ListOfUsersManager(null,
        {'addExisting': 'admin.general.addExistingAdmin', 'remove': 'admin.general.removeAdmin'},
        {}, $E('inPlaceAdministrators'), "administrator", "UIPerson", true, {}, {title: false, affiliation: false, email:true},
        {remove: true, edit: false, favorite: true, arrows: false, menu: false}, ${ administrators | n,j});

</script>
