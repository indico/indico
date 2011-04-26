<table class="groupTable">
    <tr>
        <td colspan="2">
            <div class="groupTitle">Details for ${ title } ${ fullName }</div>
        </td>
    </tr>
    <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat">Affiliation</span></td>
        <td class="blacktext">${ organisation }</td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">Email</span></td>
        <td class="blacktext">${ email }</td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">Address</span></td>
        <td class="blacktext"><pre>&nbsp;&nbsp;${ address }</pre></td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">Telephone</span></td>
        <td class="blacktext">${ telephon }</td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD"><span class="dataCaptionFormat">Fax</span></td>
        <td class="blacktext">${ fax }</td>
    </tr>
    <tr>
        <td>&nbsp;</td>
        <td class="blacktext">
            <form action="${ modifyUserURL }" method="POST" style="margin:0;">
                <input type="submit" class="btn" value="modify">
            </form>
        </td>
    </tr>
    <tr>
        <td colspan="2" ><div class="groupTitle">Your account(s)</div></td>
    </tr>
        <td nowrap class="dataCaptionTD">
            <span class="dataCaptionFormat">Account status</span>
        </td>
        <td bgcolor="white" nowrap valign="top" class="blacktext">
            ${ status }
            ${ activeButton }
        </td>
    </tr>
    <tr>
        <td>&nbsp;</td>
        <td class="blacktext">
            ${ identities }
        </td>
    </tr>
    <tr>
        <td colspan="2" >
            <div class="groupTitle">Special Rights</div>
        </td>
   </tr>
   <tr>
        <td nowrap class="dataCaptionTD">
            <span class="dataCaptionFormat">Category Manager</span>
        </td>
        <td class="blacktext">
            ${ categoryManager }
        </td>
    </tr>
    <tr>
        <td nowrap class="dataCaptionTD">
            <span class="dataCaptionFormat">Event Manager</span>
        </td>
        <td class="blacktext">
            ${ eventManager }
        </td>
    </tr>
</table>