% if not error:
    <script>
    function getChoice(){
        chosen = "";
        len = document.choiceButton.EAChoice.length;
        for (i = 0; i<len; i++){
            if (document.choiceButton.EAChoice[i].checked)
                chosen = document.choiceButton.EAChoice[i].value;
        }

        if(chosen == ""){
            return "None";
        }else{
            return chosen;
        }
    }
    function signEA(){
        choice = getChoice();

        if(choice == "accept"){
            // Update and store info, popup confirmation and redirect to event page.
            acceptElectronicAgreement(${conf.getId()}, "${authKey}", "${linkToEvent}");
        }else if(choice == "refuse"){
            // Popup window asking for the rejection reason...
            rejectElectronicAgreement(${conf.getId()}, "${authKey}", "${linkToEvent}");
        }else{
            var dialog = new WarningPopup($T("Warning"), $T("No choice selected! Please select one."));
            dialog.open();
        }
    }
    </script>
        <div class="EATitle">Electronic Agreement</div>
        <div ${addStyle} > <!-- if meeting/lecture reduce size... -->
            <div class="EAContent">
                <div class="EAFormSection">
                    ${detailsContent}
                </div>
                <div class="EAFormSection">
                    ${detailsAgreement}
            </div>
        </div>
% elif error == 'Already Submitted':
    <!-- Print a message error... depending if 'Error' or 'Already Submited'-->
        <div class="EATitle">Electronic Agreement</div>
        <div ${addStyle} > <!-- if meeting/lecture reduce size... -->
            <div class="EAContent">
                <div class="EAFormSection">
                    ${detailsAlreadySub}
                </div>
            </div>
        </div>
% elif error == 'Error':
    Sorry, an error appear, please go back and try again.
% endif