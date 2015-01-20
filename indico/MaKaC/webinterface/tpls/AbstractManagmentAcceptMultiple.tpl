<script type="text/javascript">

function showAbstracts()
{
    var listOfAbstracts = ${ listOfAbstracts };
    var ul = Html.ul({id: '',style:{listStyle: 'circle', marginLeft:'-25px'}});
    for (var i = 0; i < listOfAbstracts.length; i++)
    {
        ul.append(Html.li('', listOfAbstracts[i]));
    }
    var popup = new AlertPopup("List of abstracts", ul);
    popup.open();
}


</script>

<div class="groupTitle">${ _("Accepting %s abstracts")%abstractsQuantity }</div>
<em>${ _("Click")} <a href="javascript:showAbstracts()">${ _("here")}</a> ${_("to see the list of the abstracts you are accepting")}</em>
<br/><br/>
<table width="100%" align="center" border="0">
    <tr>
        <td bgcolor="white">
            <table>
                <tr>
                    <form action=${ acceptURL } method="POST">
                    <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Comments")}</span></td>
                    <td><textarea name="comments" rows="6" cols="50"></textarea></td>
                </tr>
                <tr>
                    <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Destination track")}</span></td>
                    <td>
                        <select name="track">
                            <option value="conf">--${ _("no track") }--</option>
                            % for t in tracks:
                                <option value=${ t.getId() } > ${ t.getTitle() } </option>
                            % endfor
                        </select>
                    </td>
                </tr>
                <tr>
                    <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Destination session")}</span></td>
                    <td>
                        <select name="session">
                                <option value="conf">--${ _("no session") }--</option>
                                % for session in sessions:
                                    <option value=${ session.getId() } >${ session.getTitle() }</option>
                                % endfor
                        </select>
                    </td>
                </tr>
                <tr>
                    <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Type of contribution")}</span></td>
                    <td>
                        <select name="type">
                            <option value="not_defined">--${ _("not defined") }--</option>
                            % for type in self_._conf.getContribTypeList():
                                <option value=${ type.getId() } >${ type.getName() }</option>
                            % endfor
                        </select>
                    </td>
                </tr>
                <tr>
                    <td nowrap class="titleCellTD"><span class="titleCellFormat">${ _("Email Notification")}</span></td>
                    <td>
                        <input type="checkbox" name="notify" value="true" checked>${ _(" Automatic Email Notification")}
                    </td>
                </tr>
            </table>
            <br>
        </td>
    </tr>
    <tr>
        <td valign="bottom" align="left">
            <table valign="bottom" align="left">
                <tr>
                    <td valign="bottom" align="left">
                        <input type="submit" class="btn" name="accept" value="${ _("accept")}">
                    </td>
                    </form>
                    <form action=${ cancelURL } method="POST">
                    <td valign="bottom" align="left">
                        <input type="submit" class="btn" name="cancel" value="${ _("cancel")}">
                    </td>
                    </form>
                </tr>
            </table>
        </td>
    </tr>
</table>
