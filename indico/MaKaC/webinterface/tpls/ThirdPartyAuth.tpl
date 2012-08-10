<div class="container" style="width: 100%; margin: 50px auto; max-width: 800px">

<div class="groupTitle" style="margin-bottom: 30px; font-size: 25pt;    ">${ _("Authorize a third party application")}</div>

<p>${ _("Do you allow ")}<b>${ third_party_app }</b>${ _(" to access your data in Indico?") }</p>
<table>
    <tr>
        <td class="titleCellTD">&nbsp;</td>
        <td class="contentCellTD">
            <div class="yellowButton loginButton">
                <a href="${ returnURL }?user_id=${ user_id }&response=accept&third_party_app=${ third_party_app }&callback=${ callback }" id="acceptButton" name="accept">${ _("Allow")}</a>
            </div>
        </td>
        <td class="contentCellTD">
            <div class="yellowButton loginButton">
                <a href="${ returnURL }?user_id=${ user_id }&response=refuse&third_party_app=${ third_party_app }&callback=${ callback }" id="refuseButton" name="refuse">${ _("Refuse")}</a>
            </div>
        </td>
    </tr>
</table>
</div>
