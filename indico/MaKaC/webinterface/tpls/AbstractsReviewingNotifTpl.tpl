<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.common import Config %>
<div style="padding-bottom:35px;">
<table class="groupTable">
    <tr>
        <td id="reviewingModeHelp" colspan="5" class="groupTitle">
            ${ _("Email notification templates")}
        </td>
    </tr>
    <tr>
        <td style="padding-top:5px; padding-left:5px;">
            <span class="italic">${ _("Add the templates for the emails which will be sent to the primary authors or submitters when their abstracts change the status to Accepted, Rejected or Merged.")}</em>
        </td>
    </tr>
    <tr>
        <form action=${ remNotifTplURL } method="POST">
        <td bgcolor="white" width="100%" class="blacktext">
            <table width="98%" border="0" align="right" style="padding-top: 10px; padding-bottom: 10px;">
                % for tpl in conf.getAbstractMgr().getNotificationTplList():
                <tr>
                    <td bgcolor="white" nowrap>
                        <a href='${ str(urlHandlers.UHConfModCFANotifTplUp.getURL(tpl)) }'><img src='${ str(Config.getInstance().getSystemIconURL("upArrow")) }' border="0" alt=""></a>
                        <a href='${ str(urlHandlers.UHConfModCFANotifTplDown.getURL(tpl)) }'><img src='${ str(Config.getInstance().getSystemIconURL("downArrow")) }' border="0" alt=""></a>
                        <input type="checkbox" name="selTpls" value='${ str(tpl.getId()) }'>
                    </td>
                    <td bgcolor="white" align="left" nowrap><a href='${ str(urlHandlers.UHAbstractModNotifTplDisplay.getURL(tpl)) }'>${ tpl.getName() }</a></td>
                    <td>&nbsp;<td>
                    <td bgcolor="white" align="left" width="90%"><font size="-1">${ tpl.getDescription() }</font></td>
                </tr>
                % endfor
            </table>
        </td>
        <table>
        <tr>
            <td valign="center" align="left">
                <input type="submit" class="btn" value="${ _("remove")}">
            </td>
        </form>
            <td valign="center" align="left">
            <form action=${ addNotifTplURL } method="POST">
                <input type="submit" class="btn" value="${ _("add")}">
            </form>
            </td>
        </tr>
        </table>
    </tr>
</table>
</div>