
    <!-- CONTEXT HELP DIVS -->
    <div id="tooltipPool" style="display: none">
        <div id="features" class="tip">
            ${ _("""- <strong>News</strong>: will display "latest news" on the Indico home page and menu<br/>
            - <strong>Receive important notifications</strong>: will keep the administrators up to date with all the newest Indico features and security warnings.""")}
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
       <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">${ _("Technical contact email")}</span></td>
       <td bgcolor="white" width="100%" valign="top" class="blacktext">${instanceTrackingEmail}</td>
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
    % if _app.debug:
        <tr>
          <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat"> ${ _("Debug mode")}</span></td>
          <td bgcolor="white" width="100%" valign="top" class="blacktext" style="color: red;">${ _('Enabled') }</td>
        </tr>
    % endif
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
                    <td><ul id="inPlaceAdministrators" class="user-list"></ul></td>
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
        {}, $E('inPlaceAdministrators'), "administrator", "item-user", false, {}, {title: false, affiliation: false, email:true},
        {remove: true, edit: false, favorite: true, arrows: false, menu: false}, ${ administrators | n,j}, null, null, null, false);

</script>
