<br><table width="100%" align="center">
    <tr>
        <td align="center">
            <form action=${ submitURL } method="POST">
            ${ submitBtn }
            </form>
        </td>
    </tr>
    <tr>
        <td>
        <table align="center" width="95%" border="0" style="border: 1px solid #777777;">
            <tr>
                <td>&nbsp;</td>
            </tr>
            <tr>
                <td>
                    <table align="center" width="95%" border="0">
                        ${ withdrawnNotice }
                    <tr>
                        <td align="center">${ modifIcon }<font size="+1" color="black"><b>${ title }</b></font></td>
                    </tr>

                    <tr>
                        <td>
                            <table align="center">
                                <tr>
                                    <td>${ description }</td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <tr>
                        <td>
                            <table align="center" width="90%">
                                <tr>
                                    <td align="right" valign="top" class="displayField"><b> ${ _("Id")}:</b></td>
                                    <td>${ id }</td>
            </tr>
            ${ location }
            <tr>
                <td align="right" valign="top" class="displayField"><b> ${ _("Starting date")}:</b></td>
            <td width="100%">
                <table cellspacing="0" cellpadding="0" align="left">
                <tr>
                    <td align="right">${ startDate }</td>
                <td>&nbsp;&nbsp;${ startTime }</td>
                </tr>
                </table>
            </td>
            </tr>
            <tr>
                <td align="right" valign="top" class="displayField"><b> ${ _("Duration")}:</b></td>
            <td width="100%">${ duration }</td>
            </tr>
                    ${ contribType }
                    ${ primaryAuthors }
                    ${ coAuthors }
                    ${ speakers }
                    % if Contribution.canUserSubmit(self_._aw.getUser()) or Contribution.canModify(self_._aw):
                    <td class="displayField" nowrap="" align="right" valign="top">
                        <b>${ _("Material:")}</b>
                    </td>
                    <td width="100%" valign="top">
                        ${MaterialList}
                    </td>
                    % else:
                        ${ material }
                    % endif
                    <tr><td>&nbsp;</td></tr>
                    ${ inSession }
                    ${ inTrack }
                    <tr><td>&nbsp;</td></tr>
                    ${ subConts }
                 </table>
                 </td>
              </tr>
              </table>
           </td>
        </tr>
        </table>
    </td>
</tr>
<tr>
    <td align="center">
        <form action=${ submitURL } method="POST">
        ${ submitBtn }
        </form>
    </td>
</tr>
</table>
