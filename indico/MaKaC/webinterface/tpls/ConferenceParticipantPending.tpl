<%page args="id, pending, conference"/>
<% from MaKaC.common.timezoneUtils import nowutc %>
<tr id="pending${id}" class="participant">
    <td width="3%" valign="top" align="right" class="CRLabstractDataCell">
    % if nowutc() < conference.getStartDate() :
        <input type="checkbox" id="checkPending${id}" value="${id}" />
    % endif
    </td>
    <td class="CRLabstractDataCell" valign="top" id="namePending${id}">
         % if nowutc() < conference.getStartDate() :
            <a href="#" id="pendingEdit${id}">${pending.getName()}</a>
         % else:
            ${pending.getName()}
         % endif:
    </td>
    <td class="CRLabstractDataCell" valign="top" id="affilitationPending${id}">${pending.getAffiliation()}</td>
    <td class="CRLabstractDataCell" valign="top" id="emailPending${id}">${pending.getEmail()}</td>
    <td class="CRLabstractDataCell" valign="top" id="addressPending${id}">${pending.getAddress()}</td>
    <td class="CRLabstractDataCell" valign="top" id="phonePending${id}">${pending.getTelephone()}</td>
    <td class="CRLabstractDataCell" valign="top" id="faxPending${id}">${pending.getFax()}</td>
</tr>

<script type="text/javascript">
    $('#pendingEdit${id}').click(function(){
        var onSuccess = function(result){
            $('#pending${id}').replaceWith(result);
            $('#pending${id}').effect("highlight",{}, 1500);
            actionPendingRows();
        };
        var userData = {};
        userData["id"] = '${id}';
        userData["title"] = '${pending.getTitle()}';
        userData["surName"] = '${pending.getFamilyName()}';
        userData["name"] = '${pending.getFirstName()}';
        userData["email"] = '${pending.getEmail()}';
        userData["address"] = '${pending.getAddress()}';
        userData["affiliation"] = '${pending.getAffiliation()}';
        userData["phone"] = '${pending.getTelephone()}';
        userData["fax"] = '${pending.getFax()}';
        new ApplyForParticipationPopup('${self_._conf.getId()}','event.participation.editPending',  $T('Edit pending participant'), userData, onSuccess, true);
    });
</script>
