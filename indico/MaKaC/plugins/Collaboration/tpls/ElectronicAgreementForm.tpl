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
        <div ${'style="margin: 0 10%;"' if conf.getType() != 'conference' else ''}>
            <div class="EAContent">
              <div class="EAFormSection">
                <p>Dear ${speaker.getDirectFullName()},</p>
                <p>you have been contacted because you have been scheduled to give a talk for the following event:</p>
                <table class="EATable">
                  <tr>
                    <td class="EAInfo">Event Title:</td>
                    <td>${conf.getTitle()}</td>
                  </tr>
                  <tr>
                    <td class="EAInfo">Held on:</td>
                    <td>${confDate}</td>
                  </tr>
                  <tr>
                    <td class="EAInfo">Place:</td>
                    <td>${locationText}</td>
                  </tr>

                % if showContributionInfo:
                </table>
                <p>Your contribution details are the following:</p>
                <table class="EATable">
                  <tr>
                    <td class="EAInfo">Talk:</td>
                    <td>${cont.getTitle()}</td>
                  </tr>
                  % if cont.getDescription():
                  <tr>
                    <td class="EAInfo">Description:</td>
                    <td>${cont.getDescription()}</td>
                  </tr>
                  % endif
                  <tr>
                    <td class="EAInfo">Scheduled on:</td>
                    <td>${contDate}</td>
                  </tr>
                  <tr>
                    <td class="EAInfo">Place:</td>
                    <td>${locationText}</td>
                  </tr>
                </table>
                % endif
                </table>
              </div>
              <div class="EAFormSection">
                <div>
                  <p>${requestText}</p>
                  <p>[blablablabla]</p>
                </div>
                <form name="choiceButton" class="EAChoiceButton">
                  <div><input type="radio" name="EAChoice" value="accept">I confirm that I read the Electronic Agreement form and <strong>accept</strong>.</input></div>
                  <div><input type="radio" name="EAChoice" value="refuse">I confirm that I read the Electronic Agreement form but I <strong>refuse</strong>.</input></div>
                  <div><input type="button" name="sendChoice" value="Submit" onclick="return signEA()"/></div>
                </form>
              </div>
              </div>
            </div>
% elif error == 'Already Submitted':
        <div class="EATitle">Electronic Agreement</div>
        <div ${'style="margin: 0 10%;"' if conf.getType() != 'conference' else ''}>
            <div class="EAContent">
                <div class="EAFormSection">
                  <p>Dear ${speaker.getDirectFullName()},</p>
                  <p>${outcomeText}</p>
                  <p>Thus, you don't have access to this page anymore. Therefore, if you want to modify your choice, you have to contact the manager.</p>

                </div>
            </div>
        </div>
% elif error == 'Error':
    ${"Sorry, there was an error, please go back and try again." | _}
% endif
