    <form action=# method="post" name="electronicAgreementForm" onSubmit="return atLeastOneSelected()">
        <div class="groupTitle">Electronic Agreement</div>

    % if canShow:
        <div>
            <div class="optionsBlock">
                <div>
                    <img src="${emailIconURL}" style="vertical-align:middle; width:24px">
                    <span style="vertical-align:middle" class="subtitle">Email notification</span>
                </div>
                <div id="inPlaceEditNotifyElectronicAgreement"></div>
            </div>
            <div class="RRNoteText">
                ${_("""<p>Before any recording can be published, each speaker must sign the {0}.
                         There are two ways of doing so:</p>
                         <p>Either:</p>
                         <ul>
                            <li><span style="font-weight:bold;">Electronic signature (<strong>recommended</strong>):</span> Select the speakers who need to sign (from the list below) and click on the "Send Email" button.
                            </li>
                         </ul>
                         <p><em>or</em></p>
                         <ul>
                            <li>
                              Ask the speaker to sign the {1}. Then, <span style="font-weight:bold;">Upload</span> the corresponding line in the list below.
                            </li>
                         </ul>""").format(agreementName, urlPaperAgreement)}
            </div>
        </div>

        <!-- Decide if keep or not... (if T. notice or not) -->
        <!-- <div align="right">
            % if signatureCompleted:
                <label style="background-color:green;">${_("All the contributions are ready to be published")}</label>
            % else:
                <label style="background-color:red;">${_("Some contributions cannot be published")}</label>
            % endif
        </div> -->

        <div id="tooltipPool1" style="display: none">
          <div id="requestType" class="tip">
            <strong>Request type involved for Electronic Agreement</strong>
            <ul>
              <li><strong>REC</strong>: Only the recording has been requested.</li>
              <li><strong>WEBC</strong>: Only the webcast has been requested.</li>
              <li><strong>REC/WEBC</strong>: Both recording and webcast have been requested.</li>
              <li><strong>NA</strong>: Information not available.</li>
            </ul>
          </div>
        </div>

        <div id="tooltipPool2" style="display: none">
          <div id="status" class="tip">
            <strong>Status Legend</strong>
            <ul>
              <li><strong>No Email</strong>: Speaker does not have an Email address.</li>
              <li><strong>Not Signed</strong>: Agreement not signed.</li>
              <li><strong>Pending...</strong>: Email sent to the speakers, waiting for signature.</li>
              <li><strong>Signed</strong>: Agreement signed electronically.</li>
              <li><strong>Uploaded</strong>: Agreement signed uploading the form.</li>
              <li><strong>Refused</strong>: Agreement refused.</li>
            </ul>
          </div>
        </div>

        <table cellspacing="0" align="left" width="100%" valign="top">
            <tr>
                <td colspan="11" style="border-bottom:2px solid #777777;padding-top:5px" valign="bottom" align="left">
                    <table>
                        <tr>
                            <td valign="bottom" align="left">
                                <input type="button" class="btn sendEmail" name="sendEmail" value="${_("Send Email")}" />
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            <tr>
                <td colspan=4 style="padding: 5px 0px 10px;" nowrap>
                    Select: <a style="color: #0B63A5;" alt="Select all" id="selectAll"> All</a>,
                    <a style="color: #0B63A5;" alt="Unselect all" id="deselectAll">None</a>
                </td>
            </tr>
            <tr>
                <td></td>
            </tr>
            <tr>
                <td></td>
                <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888; border-right:5px solid #FFFFFF">
                    <a href="${speakerSortingURL}" > ${_("Speaker ")} ${speakerImg}</a>
                </td>
                <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888; border-right:5px solid #FFFFFF">
                    ${_("Email")}
                </td>
                <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888; border-right:5px solid #FFFFFF">
                    <a href="${statusSortingURL}" > ${_("Status ")} ${statusImg}${contextHelp('status')}</a>
                </td>
                <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888; border-right:5px solid #FFFFFF">
                    <a href="${reqTypeSortingURL}" > ${_("Request Type ")} ${reqTypeImg}${contextHelp('requestType')}</a>
                </td>
                <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888; border-right:5px solid #FFFFFF;">
                    <a href= "${contSortingURL}" > ${_("Contribution ")} ${contImg}</a>
               </td>
               <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF">
                    ${_("Upload Agreement")}
               </td>
            </tr>
            <tr>
                <td>
                    <tbody id="items">
                      % for spkId, spkName, status, contribId, reqType, enabled in contributions:
                          <%include file="ElectronicAgreementItems.tpl" args="spkId=spkId, spkName=spkName, status=status, contribId=contribId, reqType=reqType, enabled=enabled, canModify=canModify"/>
                      % endfor
                    </tbody>
                </td>
            </tr>
            <tr>
                <td colspan="11" style="border-top: 2px solid #777777; padding-top: 3px;" valign="bottom" align="left">
                    <table>
                        <tr>
                            <td valign="bottom" align="left"><input type="button" class="btn sendEmail" name="Send Email" value="${_("Send Email")}"/>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    % else:
        <span class="RRNoteText">
                ${_("Before any lecture recording can be published, each speaker must sign the %s.")%agreementName} <br/>
                ${_("Options and tools for managing and tracking these %s will appear on this page as soon as your recording request is accepted.")%agreementName}<br/>
                ${_("Please come back here when your request is accepted.")}
        </span>
    % endif
    </form>

<script type="text/javascript">

$(function() {
    $("#inPlaceEditNotifyElectronicAgreement").append($(new SwitchOptionButton("collaboration.toggleNotifyElectronicAgreementAnswer",{confId:${conf.getId()}}, $T("Notify managers when Electronic Agreement is accepted/rejected"),$T("Saved"), ${notifyElectronicAgreementAnswer | n,j} , ${not canModify | n,j}).draw()));

    $('.speakerLine input').change(function() {
        if (this.checked) {
            $(this).parents('.speakerLine').addClass('selected');
        } else {
            $(this).parents('.speakerLine').removeClass('selected');
        }
    });

    $('.sendEmail').click(function(){
        // make sure at least one is selected
        if($('.speakerLine input:not(:disabled):checked').length) {
            var uniqueIdList = $('.speakerLine input:checked').map(function(){return this.id;}).toArray();
            var defaultText = "Dear {name},<br />" +
                            "<br />" +
                            'I have requested that your talk "<strong>{talkTitle}</strong>" during the event "<strong>' + ${conf.getTitle()| n,j} +'</strong>" be recorded and published.<br />' +
                            'In order to allow the recording team to publish the video recording, we would need you to sign the speaker release form at this page:' +
                            "<br/><br/> {url} <br/>"+
                            "<br/>" +
                            "Best Regards,<br/><br />" +
                            ${user.getStraightFullName(upper=False) | n,j};
            var legends = {'url':$T('field containing the url of the electronic agreement. (This field is mandatory)'),
                    'talkTitle':$T('field containing the talk title. (This field is mandatory)'),
                    'name':$T('field containing the full name of the speaker.')};
            var popup = new SpeakersEmailPopup(${conf.getTitle()| n,j}, ${conf.getId()}, uniqueIdList, ${fromList|n,j} , ${user.getId()}, defaultText, legends);
            popup.open();
        } else {
            var dialog = new WarningPopup($T("Warning"), $T("No entry selected! Please select at least one."));
            dialog.open();
            return false;
        }
    });

    $('#selectAll').click(function() {
        $('.speakerLine input:not(:disabled)').prop('checked', true)
        $('.speakerLine input').trigger('change');
    });

    $('#deselectAll').click(function() {
        $('.speakerLine input:not(:disabled)').prop('checked', false)
        $('.speakerLine input').trigger('change');
    });

    $('.contName').mouseover(function(event) {
        IndicoUI.Widgets.Generic.tooltip(this, event,
            '<ul style="list-style-type:none;padding:3px;margin:0px">'+
           '<li>'+this.name+'<\/li><\/ul>'
        );
    });

    $('.reject').mouseover(function(event) {
        IndicoUI.Widgets.Generic.tooltip(this, event,
                '<ul style="list-style-type:none;padding:3px;margin:0px;"><li>'+
                '<b>Reject reason:</b> '+
                this.name+
                '</li></ul>'
        );
    });
    $('span.noUploadRights').qtip({content: $T("You do not have access to upload the Electronic Agreement"), position: {my: 'top middle', at: 'bottom middle'}});
});

</script>
