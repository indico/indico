% if not error:
    <script>
    function signEA(){
        var choice = $('input[name="EAChoice"]:checked').val();

        if(choice == "accept"){
            // Update and store info, popup confirmation and redirect to event page.
            acceptElectronicAgreement(${conf.getId() |n,j}, "${authKey}", "${linkToEvent}");
        }else if(choice == "refuse"){
            // Popup window asking for the rejection reason...
            rejectElectronicAgreement(${conf.getId() |n,j}, "${authKey}", "${linkToEvent}");
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
                  <p><strong>Do you agree with the following standard ${agreementName}:</strong></p>
                  <p>I hereby consent to the photographic, audio and video recording of my performance or
presentation at CERN. The term “performance or presentation” includes any material
incorporated therein including but not limited to text, images and references.</p>
<p>
I hereby grant CERN a royalty-free license to use my image and name as well as the aforementioned
recordings, in whole or in part, and to broadcast or distribute same in any format, in
the furtherance of CERN’s scientific and educational mission. I agree to the modification of the
afore-mentioned recordings provided that the substance of the performance or presentation is
preserved.</p>
<p>
I hereby confirm that the content of my performance or presentation does not infringe the
copyright, intellectual property or privacy rights of any third party. I have cited and credited any
third party contribution in accordance with applicable professional standards and legislation in
matters of attribution.</p>
                </div>
                <form name="choiceButton" class="EAChoiceButton">
                  <div><input type="radio" name="EAChoice" value="accept">I <strong>agree</strong>.</input></div>
                  <div><input type="radio" name="EAChoice" value="refuse">I <strong>disagree</strong> (my talk will not be published).</input></div>
                  <div style="margin-top: 30px">
                    <input type="button" name="sendChoice" value="Submit" onclick="return signEA()"/>
                  </div>
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
