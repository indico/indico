<script type="text/javascript">
    $(function(){
        var onSuccess = function(result){
            if(result.msg){
                (new AlertPopup($T("Success"),result.msg)).open();
            }
            if (result.listParticipants){
                if( $("#eventParticipants").length==0){
                    var trParticipants=$(Html.tr({id:"eventParticipants"},
                                                 Html.td({className:"leftCol"},$T("Participants")),
                                                 Html.td({id:"eventListParticipants"},"")).dom);
                    if ($("#eventDescription").length==0){
                        $("#eventDetails").prepend(trParticipants);
                    }else{
                        $("#eventDescription").after(trParticipants);
                    }
                }
                $("#eventListParticipants").text(result.listParticipants).effect("highlight",{},3000);
            }
        };

        var allowEdit = true;
        % if currentUser:
            allowEdit = false;
            var userData = {"id": '${currentUser.getId()}',
                            "title": '${currentUser.getTitle()}',
                            "surName": ${currentUser.getFamilyName() | n,j},
                            "name": ${currentUser.getName() | n,j},
                            "email": '${currentUser.getEmail()}',
                            "address": ${currentUser.getAddress() | n,j},
                            "affiliation": ${currentUser.getAffiliation() | n,j},
                            "phone": '${currentUser.getTelephone()}',
                            "fax": '${currentUser.getFax()}'
                           };
        % else:
           var userData = {};
        % endif
            $('#applyLink').click(function(){new ApplyForParticipationPopup('${conf.getId()}','event.participation.applyParticipant',
                    $T('Apply for participation'), userData, onSuccess, allowEdit);});
    });
</script>
