<br>
<table width="100%" align="center">
    <tr>
        <td><br></td>
    </tr>
    <tr>
        <td>
            <table align="center" width="95%" border="0" style="border: 1px solid #777777;">
                <tr><td>&nbsp;</td></tr>
                <tr>
                    <td>
                        <table align="center" width="95%" border="0">
                            <tr>
                                <td colspan="2" align="center">${ modifyItem }<b><font size="+1" color="black">${ title }</font></b></td>
                            </tr>
                            <tr>
                                <td width="100%" colspan="3">&nbsp;<td>
                            </tr>
                            <tr>
                                <td align="left" colspan="3">
                                    <table width="95%" align="center" valign="top" border="0">
                                        % if showAttachedFiles:
                                            <tr>
                                                <td align="right" valign="top"
                                                    class="displayField"><b>${ _("Abstract files")}:</b></td>
                                                <td>
                                                % for file in abstractAttachments:
                                                    <div style="padding-bottom:3px;"><a href=${ file["url"] }>${ file["file"]["fileName"] }</a></div>
                                                % endfor
                                                </td>
                                            </tr>
                                        % endif
                                        <tr>
                                            <td align="right" valign="top"
                                                class="displayField"><b>${ _("Id")}:</b></td>
                                            <td>${ id }</td>
                                        </tr>
                                        ${ material }
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
</table>
<br>
