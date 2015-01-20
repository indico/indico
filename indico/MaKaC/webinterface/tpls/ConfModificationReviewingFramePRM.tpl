<% from MaKaC.paperReviewing import ConferencePaperReview %>
<% from MaKaC.common.fossilize import fossilize %>

<table width="90%" align="left" border="0" style="padding-top:10px;">
    <tbody>
    <tr>
        <td id="revControlPRMHelp"  colspan="3" class="groupTitle">${ _("Step 1 - Assign managers of paper reviewing")}</td>
    </tr>
    <tr>
        <td colspan="3">
            % if ConfReview.getEnablePRMEmailNotif():
                <div style="padding:5px; color:gray;">
                    <span class="italic">${_("An automatically generated e-mail will be sent to newly assigned Paper Review Managers.")}</span><br>
                    <span class="italic">${ _("You  can  modify this from the Paper Reviewing ")}<a href="${ urlHandlers.UHConfModifReviewingPaperSetup.getURL(ConfReview.getConference()) }">${ _("Setup.")}</a></span>
                </div>
            % endif
        </td>
    </tr>
    </tbody>
</table>
<tr><td>
<table width="60%" style="padding-left:20px;">
    <tbody>
    <tr>
        <td class="subGroupTitle">${ _("Managers") }</td>
    </tr>
    <tr>
        <td class="questionContent" style="padding-top:5px; padding-left:3px;">
            <span>${ _("Responsibilities: Setup, assign contributions to Referees, define team competences") }</span></span>
        </td>
    </tr>
    <tr>
        <td width="80%" style="padding-top: 5px; padding-left:3px;"><div id="PRMList"></div></td>
    </tr>
    </tbody>
</table>
</td></tr>
<br>

<script type="text/javascript">
                        var newPRMHandler = function(userList, setResult) {
                            indicoRequest(
                                'reviewing.conference.assignTeamPRM',
                                {
                                    conference: '${ Conference }',
                                    userList: userList
                                },
                                function(result,error) {
                                    if (!error) {
                                        setResult(true);
                                    } else {
                                        IndicoUtil.errorReport(error);
                                        setResult(false);
                                    }
                                }
                            );
                        };

                        var removePRMHandler = function(user, setResult) {
                            indicoRequest(
                                'reviewing.conference.removeTeamPRM',
                                {
                                    conference: '${ Conference }',
                                    user: user.get('id')
                                },
                                function(result,error) {
                                    if (!error) {
                                        setResult(true);
                                    } else {
                                        IndicoUtil.errorReport(error);
                                        setResult(false);
                                    }
                                }
                            );
                        };

                        var uf = new UserListField('managersPRUserListDiv', 'userList',
                                ${ jsonEncode(fossilize(ConfReview.getPaperReviewManagersList())) },
                                true,null,
                                true, false, null, null,
                                false, false, false, true,
                                newPRMHandler, userListNothing, removePRMHandler);
                        $E('PRMList').set(uf.draw());
</script>
