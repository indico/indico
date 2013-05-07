<%page args="participant, conference"/>
<% from MaKaC.common.timezoneUtils import nowutc %>
<tr id="participant${participant.getId()}" class="participant">
    <td class="CRLabstractDataCell" width="3%" valign="top" align="right">
        <input type="checkbox" name="participants" id="checkParticipant${participant.getId()}" value="${participant.getId()}"/>
    </td>
    <td class="CRLabstractDataCell" valign="top" id="nameParticipant${participant.getId()}">
        <a href="#" id="participantEdit${participant.getId()}">${participant.getName()}</a>
    </td>
    <td class="CRLabstractDataCell" valign="top" id="affilitationParticipant${participant.getId()}">${participant.getAffiliation()}</td>
    <td class="CRLabstractDataCell" valign="top" id="emailParticipant${participant.getId()}">${participant.getEmail()}</td>
    <td class="CRLabstractDataCell" valign="top" id="addressParticipant${participant.getId()}">${participant.getAddress()}</td>
    <td class="CRLabstractDataCell" valign="top" id="phoneParticipant${participant.getId()}">${participant.getTelephone()}</td>
    <td class="CRLabstractDataCell" valign="top" id="faxParticipant${participant.getId()}">${participant.getFax()}</td>
    <td class="CRLabstractDataCell" valign="top" id="statusParticipant${participant.getId()}">${participant.getStatus()}</td>
    <td class="CRLabstractDataCell" valign="top" id="presence${participant.getId()}">
      % if nowutc() > conference.getStartDate() and participant.isConfirmed():
        % if participant.isPresent():
          ${_("Attended")}
        % else:
          ${_("Didn't attend")}
        % endif
      % else:
          ${_("n/a")}
      % endif
    </td>
</tr>
<script type="text/javascript">
    $('#participantEdit${participant.getId()}').click(function(){
        var onSuccess = function(result){
            $('#participant${participant.getId()}').replaceWith(result);
            $('#participant${participant.getId()}').effect("highlight",{}, 1500);
            actionParticipantRows();
        };
        var userData = {};
        userData["id"] = '${participant.getId()}';
        userData["title"] = '${participant.getTitle()}';
        userData["surName"] = ${participant.getFamilyName() | n,j};
        userData["name"] = ${participant.getFirstName() | n,j};
        userData["email"] = ${participant.getEmail() | n,j};
        userData["address"] = ${participant.getAddress() | n,j};
        userData["affiliation"] = ${participant.getAffiliation() | n,j};
        userData["phone"] = '${participant.getTelephone()}';
        userData["fax"] = '${participant.getFax()}';
        new ApplyForParticipationPopup('${self_._conf.getId()}','event.participation.editParticipant',  $T('Edit participant'), userData, onSuccess, true);
    });
</script>
