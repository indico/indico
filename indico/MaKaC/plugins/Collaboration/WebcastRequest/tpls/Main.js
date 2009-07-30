{ 
    checkParams : function () {
        return {
            "permission": ["radio", false, function(option, values){
                var errors = [];
                if (!exists(values["permission"])) {
                    errors.push("Please answer if all the speakers given permission to have their talks webcasted.");
                }
                return errors;
            }],
            "lectureOptions": ["text", true, function(option, values){
                var errors = [];
                if (option == 'chooseOne') {
                    errors.push("Please choose if slides and/or chalkboards will be used.");
                }
                return errors;
            }],
            "lectureStyle": ["text", true, function(option, values){
                var errors = [];
                if (option == 'chooseOne') {
                    errors.push("Please choose a type of event.");
                }
                return errors;
            }]/*This code is commented out because it doesnt work very well.
                There where some problems with when the user chooses to choose 
                contributions. When he does not choose any, he shoud idealy
                get an error message. This was complicated by the fact that
                the code the turs stuff red does not support two things:
                    1. keeping the current onclick function of the element.
                    2. other elements controlling the thing that is red.
                might be solved in the future.
                
                Note to whoever might fix this sometime:
                    currently the entire first question is not shown,if
                    the event has no contributions.
                , "talks": ["radio", false, function(option, values){
                alert("Halloen");
                var errors = [];
                if(option){
                    if(values["talks"]=="choose"){
                        alert("Halloen1");
                        var checkboxes = values["talkSelection"];
                        if(checkboxes.length == 0){
                            alert("Halloen2");
                            errors.push("Please choose one or more talks.")
                        }
                    }
                }
                 return errors;
             }]*/
        }
    },
    
    errorHandler: function(event, error) {
        if (error.operation == "create") {
            CSErrorPopup("Could not send email to responsible",
                         [Html.span("", "There was a problem when sending the notification email to the Webcast responsible:", Html.br(), error.inner)])
        }
        if (error.operation == "edit") {
            CSErrorPopup("Could not send email to responsible",
                         [Html.span("", "There was a problem when sending the notification email to the Webcast responsible:", Html.br(), error.inner)])
        }
        if (error.operation == "remove") {
            CSErrorPopup("Could not send email to responsible",
                        [Html.span("", "There was a problem when sending the notification email to the Webcast responsible:", Html.br(), error.inner)])
        }
    },
    
    customText : function(booking) {
        if (booking.statusMessage == "Request rejected by responsible" && trim(booking.rejectionReason)) {
            return "Rejection reason: " + trim(booking.rejectionReason);
        }
    },
    
    clearForm : function () {
        var formNodes = IndicoUtil.findFormFields($E('WebcastRequestForm'));
        IndicoUtil.setFormValues(formNodes, {'talkSelectionComments':'', 'numWebcastViewers':'','numRecordingViewers':'', 'numAttendees':'', 'otherComments':''})
        <%if NwebcastCapableContributions== NContributions:%>
        /*The allTalksRB might not exist, because we hide the entire first question
         * if the event is an event without contributions.
         */
            if($E('allTalksRB') != null){
                $E('allTalksRB').dom.checked = true;
            }
        <% end %>
        <% else:%>
        /*The allTalksRB might not exist, because we hide the entire first question
         * if the event is an event without contributions.
         */
            if($E('allTalksRB') != null){
                $E('chooseTalksRB').dom.checked = true;
                $E('allTalksRB').dom.disabled = true ;
            }
        <% end %>
        //IndicoUI.Effect.disappear($E('contributionsDiv'));
        $E('permissionYesRB').dom.checked = false;
        $E('permissionNoRB').dom.checked = false;
        $E('lectureOptions').dom.value = "chooseOne";
        $E('lectureStyle').dom.value = "chooseOne";
        $E('postingUrgency').dom.value = "never";
    },
    
    onLoad : function() {
        
        if (singleBookings['WebcastRequest'] && singleBookings['WebcastRequest'].bookingParams.talks == 'choose') {
            WR_loadTalks()
            //window.contributionsLoaded = true;
        }
        /*
        " else {
            $E('contributionsRow').append(Html.td("RRContributionsColumn",Html.ul({id:'contributionList1', className:'RROptionList'})));
            $E('contributionsRow').append(Html.td("RRContributionsColumn",Html.ul({id:'contributionList2', className:'RROptionList'})));
        }
        */
        
        if(!singleBookings['WebcastRequest']) {
            callFunction('WebcastRequest','clearForm');
        }
    }
}