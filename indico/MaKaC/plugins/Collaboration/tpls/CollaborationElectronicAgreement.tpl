<script type="text/javascript">

function sendEmails(){
    if (!atLeastOneSelected())
        return false;

    var uniqueIdList = new Array();
    var form = document.electronicAgreementForm;

    if (form.cont.length){
        for (i = 0; i<form.cont.length; i++){
            if (form.cont[i].checked == true){
                uniqueIdList.push(form.cont[i].id);
            }
        }
    }else{
        if (form.cont.checked == true){
            uniqueIdList.push(form.cont.id);
        }
    }
    if (uniqueIdList.length != 0){
        var popup = new SpeakersEmailPopup( ${fossilize(conf)}, uniqueIdList, ${fromList} , ${user.getId()});
        popup.open();
    }
    return false;
}

var contFullTitle = function(event){
    IndicoUI.Widgets.Generic.tooltip(this, event,
        '<ul style="list-style-type:none;padding:3px;margin:0px">'+
        '<li>'+this.name+'<\/li><\/ul>'
    );
}

var showRejectReason = function(event){
    IndicoUI.Widgets.Generic.tooltip(this, event,
            '<ul style="list-style-type:none;padding:3px;margin:0px;"><li>'+
            '<b>Reject reason</b><br/>'+
            this.name+
            '</li></ul>'
    );
}
</script>

    <form action=# method="post" name="electronicAgreementForm" onSubmit="return atLeastOneSelected()">
        <div class="groupTitle">Electronic Agreement</div>

    % if canShow:
        <span class="RRNoteText" style="float:left;">
            ${_("""To be allowed to publish the talks, we will need every speaker to sign in an agreement.<br/>
                     To do so, two different ways are available:
                     <ol>
                        <li><span style="font-weight:bold;">Send an Email</span> containing the link to sign the agreement electronically.<br/>
                            (Select the speakers you want to send the Email and then click on the "Send Email" button.)
                        </li>
                        <li>Ask the speaker to sign the Paper Agreement that you can find
                """)}

            ${urlPaperAgreement}

             ${_("""<br/>Then, <span style="font-weight:bold;">Upload</span> it from the list below.
                           </li>
                        </ol>
                """)}
        </span>

        <!-- Decide if keep or not... (if T. notice or not) -->
        <!-- <div align="right">
            % if signatureCompleted:
                <label style="background-color:green;">${_("All the contributions are ready to be published")}</label>
            % else:
                <label style="background-color:red;">${_("Some contributions cannot be published")}</label>
            % endif
        </div> -->
        <br/>
        <br/>
        <br/>
        ${contextHelpContent}
        <table cellspacing="0" align="left" width="100%" valign="top">
            <tr>
                <td colspan="11" style="border-bottom:2px solid #777777;padding-top:5px" valign="bottom" align="left">
                    <table>
                        <tr>
                            <td valign="bottom" align="left">
                                <input type="button" class="btn" name="sendEmail" value="${_("Send Email")}" onclick="return sendEmails()" />
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            <tr>
                <td colspan=4 style='padding: 5px 0px 10px;' nowrap>
                    Select: <a style='color: #0B63A5;' alt='Select all' onclick='javascript:selectAll()'> All</a>,
                    <a style='color: #0B63A5;' alt='Unselect all' onclick='javascript:deselectAll()'>None</a>
                </td>
            </tr>
            <tr>
                <td></td>
            </tr>
            <tr>
                <td></td>
                <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888; border-right:5px solid #FFFFFF">
                    <a href=${speakerSortingURL} > ${_("Speaker ")} ${speakerImg}</a>
                </td>
                <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888; border-right:5px solid #FFFFFF">
                    ${_("Email")}
                </td>
                <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888; border-right:5px solid #FFFFFF">
                    <a href=${statusSortingURL} > ${_("Status ")} ${statusImg}${contextHelp('status')}</a>
                </td>
                <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888; border-right:5px solid #FFFFFF">
                    <a href=${reqTypeSortingURL} > ${_("Request Type ")} ${reqTypeImg}${contextHelp('requestType')}</a>
                </td>
                <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888; border-right:5px solid #FFFFFF;">
                    <a href= ${contSortingURL} > ${_("Contribution ")} ${contImg}</a>
               </td>
               <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #888;border-right:5px solid #FFFFFF">
                    ${_("Upload Agreement")}
               </td>
            </tr>
            <tr>
                <td>
                    <tbody id="items">
                        ${items}
                    </tbody>
                </td>
            </tr>
            <tr>
                <td colspan="11" style="border-top: 2px solid #777777; padding-top: 3px;" valign="bottom" align="left">
                    <table>
                        <tr>
                            <td valign="bottom" align="left"><input type="button" class="btn" name="Send Email" value="${_("Send Email")}" onclick="return sendEmails()" />
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    % else:
        <span class="RRNoteText">
                ${_("No requests have been accepted so far.")} <br/>
                ${_("In order to access this content your request has to be accepted first.")}
        </span>
    % endif
    </form>
<script>
function isSelected(element){
    var inputNodes = IndicoUtil.findFormFields($E(element))
    for (i = 0; i < inputNodes.length; i++) {
        var node = inputNodes[i];
        if (node.type == "checkbox") {
            if(node.checked == true) {
                $E(element).dom.style.backgroundColor = "#CDEB8B";
            } else {
                $E(element).dom.style.backgroundColor='transparent';
            }
        }
    }
}
function selectAll(){
    entryList = new Array();
    if (!document.electronicAgreementForm.cont.length){
        if(!document.electronicAgreementForm.cont.disabled){
            document.electronicAgreementForm.cont.checked=true;
            entryList[0] = "row"+document.electronicAgreementForm.cont.id;
        }
    }else{
        var k = 0;
        for (i = 0; i < document.electronicAgreementForm.cont.length; i++){
            if(!document.electronicAgreementForm.cont[i].disabled){
                document.electronicAgreementForm.cont[i].checked=true;
                entryList[k] = "row"+document.electronicAgreementForm.cont[i].id;
                k++;
            }
        }
    }

    for(j = 0; j < entryList.length; j++){
        isSelected(entryList[j]);
    }
}

function deselectAll(){
    entryList = new Array();
    if (!document.electronicAgreementForm.cont.length){
        document.electronicAgreementForm.cont.checked=false;
        entryList[0] = "row"+document.electronicAgreementForm.cont.id;
    }else{
        for (i = 0; i < document.electronicAgreementForm.cont.length; i++){
            document.electronicAgreementForm.cont[i].checked=false;
            entryList[i] = "row"+document.electronicAgreementForm.cont[i].id;
        }
    }

    for(j = 0; j < entryList.length; j++)
        isSelected(entryList[j]);
}

function atLeastOneSelected() {
    if(document.electronicAgreementForm.cont){
        if (!document.electronicAgreementForm.cont.length){
            if (document.electronicAgreementForm.cont.checked)
                return true;
        }else{
            for (i = 0; i < document.electronicAgreementForm.cont.length; i++){
                if (document.electronicAgreementForm.cont[i].checked)
                    return true;
            }
        }
    }
    var dialog = new WarningPopup($T("Warning"), $T("No entry selected! Please select at least one."));
    dialog.open();

    return false;
}

function onMouseOver(element) {
    if ($E(element).dom.style.backgroundColor ==='transparent') {
       $E(element).dom.style.backgroundColor='rgb(255, 246, 223)';
    }
}

function onMouseOut(element) {
    var inputNodes = IndicoUtil.findFormFields($E(element))
    for (i = 0; i < inputNodes.length; i++) {
        var node = inputNodes[i];
        if (node.type == "checkbox") {
            if(node.checked !== true) {
                $E(element).dom.style.backgroundColor='transparent';
            } else {
                $E(element).dom.style.backgroundColor = "#CDEB8B";
            }
        }
    }
}

</script>
