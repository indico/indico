<table width="100%" cellspacing="0" align="center" border="0">
    <tr>
       <td nowrap colspan="10">
            <div class="CRLgroupTitleNoBorder">${ _("Displaying")} <span id="numberParticipants" style="font-weight: bold;">${numberPending}</span>
                 ${_("pending")} <span id="numberParticipantsText">${ _("participant") if numberPending == 1 else _("participants")}</span>
            </div>
        </td>
    </tr>
    % if not conferenceStarted:
        <tr id="headPanel" style="box-shadow: 0 4px 2px -2px rgba(0, 0, 0, 0.1);" class="follow-scroll">
            <td valign="bottom" width="100%" align="left" style="padding-top:5px;" colspan="9">
                <table>
                    <tr>
                        <td valign="bottom" align="left">
                            <ul style="margin-top:0px;" id="button-menu">
                              <li class="left"><a href="#" id="accept">${ _("Accept")}</a></li>
                              <li class="right arrow" id="reject"><a href="#">${ _("Reject")}</a>
                                <ul>
                                  <li><a href="#" id="reject_with_mail">${ _("With email notification")}</a></li>
                                  <li><a href="#" id="reject_no_mail">${ _("No email notification")}</a></li>
                                </ul>
                              </li>
                            </ul>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        <tr id="selectBar" style="display:none">
            <td colspan=10 style="padding: 5px 0px 10px;" nowrap>
            Select: <a style="color: #0B63A5;" id="selectAll"> All</a>, <a style="color: #0B63A5;" id="deselectAll">None</a>
            </td>
        </tr>
    % endif
    <tr id="headPending">
        <td nowrap="" align="right" width="3%" style="border-bottom: 1px solid #DDDDDD;" class="titleCellFormat"></td>
        <td style="border-bottom: 1px solid #DDDDDD; padding-left:5px" class="titleCellFormat">
            ${_("Name")}
        </td>
        <td style="border-bottom: 1px solid #DDDDDD; padding-left:5px" class="titleCellFormat">
            ${_("Affiliation")}
        </td>
        <td style="border-bottom: 1px solid #DDDDDD; padding-left:5px" class="titleCellFormat">
            ${_("Email")}
        </td>
        <td style="border-bottom: 1px solid #DDDDDD; padding-left:5px" class="titleCellFormat">
            ${_("Address")}
        </td>
        <td style="border-bottom: 1px solid #DDDDDD; padding-left:5px" class="titleCellFormat">
            ${_("Telephone")}
        </td>
        <td style="border-bottom: 1px solid #DDDDDD; padding-left:5px" class="titleCellFormat">
            ${_("Fax")}
        </td>
    </tr>
    <tr id="noPendingInfo">
        <td colspan=10 style="font-style: italic; padding:15px 0px 15px 15px; border-bottom: 1px solid #DDDDDD;" nowrap>
            <span class="collShowBookingsText">${_("There are no pending participants yet")}</span>
        </td>
    </tr>
    % for key, p in pending:
         <%include file="ConferenceParticipantPending.tpl" args="id=key, pending=p,conference=conf"/>
    % endfor
</table>

<script type="text/javascript">

$(function() {
    $("#button-menu").dropdown();
});

var actionPendingRows = function(){
    $("input:checkbox[id^=checkPending]").click(function(){
        if(this.checked){
            $(this).parents('tr[id^=pending]').css('background-color',"#CDEB8B");
        }else{
            $(this).parents('tr[id^=pending]').css('background-color',"transparent");
        }
    });

    $("tr[id^=pending]").hover(function () {
        if($(this).find('input:checkbox:checked[id^=checkPending]').size() == 0){
            $(this).css({'background-color' : 'rgb(255, 246, 223)'});
        }}
        , function () {
          if($(this).find('input:checkbox:checked[id^=checkPending]').size() > 0){
              $(this).css('background-color',"#CDEB8B");
          }else{
              $(this).css('background-color',"transparent");
          }
    });
};

var checkNumberPending = function(){
    $('#numberParticipants').text($('input:checkbox[id^=checkPending]').length);
    if($('input:checkbox:checked[id^=checkPending]').length == 1) {
        $('#numberParticipantsText').text("participant");
    } else {
        $('#numberParticipantsText').text("participants");
    }
    if($('tr[id^=pending]').length == 0){
        $('#selectBar, #headPending').hide();
        $('#noPendingInfo').show();
    }else{
        $('#selectBar, #headPending').show();
        $('#noPendingInfo').hide();
    }
};

IndicoUI.executeOnLoad(function(){
    var rejectMenu = null;

    actionPendingRows();
    checkNumberPending();

    $("#selectPending").click(function(){
        if($(this).attr('checked')){
            $('input:checkbox[id^=checkPending]').attr('checked', 'checked');
            $('input:checkbox[id^=checkPending]').parents('tr[id^=pending]').css('background-color',"#CDEB8B");
        }else{
            $('input:checkbox[id^=checkPending]').removeAttr('checked');
            $('input:checkbox[id^=checkPending]').parents('tr[id^=pending]').css('background-color',"transparent");
        }
    });


    var atLeastOneParticipantSelected = function(){
        if ($('input:checkbox:checked').length>0){
            return true;
        } else{
            new WarningPopup($T("Warning"), $T('No pending participant selected! Please select at least one.')).open();
            return false;
        }
    };

    var pendingHandler = function(){
        $('input:checkbox:checked[id^=checkPending]').parents('tr[id^=pending]').remove();
        checkNumberPending();
    };

    var actionUsers = function(method){
        var arrayChecked=[];
        if (atLeastOneParticipantSelected()){
            $('input:checkbox:checked').each(function() {
                   arrayChecked.push($(this).val());
            });

        var killProgress = IndicoUI.Dialogs.Util.progress("Processing...");
        jsonRpc(Indico.Urls.JsonRpcService, method,
                { confId: '${self_._conf.getId()}',
                  userIds: arrayChecked},
                function(result, error){
                    killProgress();
                    if (exists(error)) {
                        IndicoUtil.errorReport(error);
                    } else {
                        pendingHandler();
                    }
                });
        return false;
    }};

    var composeEmail = function(){
        var participantsChecked={};
        if (atLeastOneParticipantSelected()){
            $("input:checkbox:checked").each(function() {
                participantsChecked[$(this).val()] = $(this).parent().siblings("[id^=namePending]").children("[id^=pending]").text();
            });
            var subject = 'Your application for attendance in \'{0}\' declined'.format(${conf.getTitle()| n,j});
            var body = 'Dear {name},<br/><br/>' +
                        'your request to attend the \'{confTitle}\' has been declined by the event manager.<br/>';
            var legends = {'confTitle':$T('field containing the conference title.'),
                           'name':$T('field containing the full name of the participant.')};
            var popup = new ParticipantsEmailPopup($T("Send mail to the participants"),"${conf.getTitle()}", ${conf.getId()}, 'event.participation.rejectPendingWithEmail', participantsChecked, '${currentUser.getStraightFullName()}' ,subject, body, legends, pendingHandler);
            popup.open();
        }
        return false;
    };

    $('#selectAll').click(function () {
        $('input:checkbox[id^=checkPending]').attr('checked', 'checked');
        $('input:checkbox[id^=checkPending]').parents('tr[id^=pending]').css('background-color',"#CDEB8B");
    });

    $('#deselectAll').click(function () {
        $('input:checkbox[id^=checkPending]').removeAttr('checked');
        $('input:checkbox[id^=checkPending]').parents('tr[id^=pending]').css('background-color',"transparent");
    });

    $('#accept').bind('menu_select', function(){
       actionUsers("event.participation.acceptPending")
    });

    $('#reject_with_mail').bind('menu_select', function(){
        return composeEmail();
    });

    $('#reject_no_mail').bind('menu_select', function(){
        return actionUsers("event.participation.rejectPending");
    });

    $(window).scroll(function(){
        IndicoUI.Effect.followScroll();
    });
});
</script>
