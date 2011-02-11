<% from MaKaC.reviewing import ConferencePaperReview %>
<% from MaKaC.common.fossilize import fossilize %>

<table width="90%" align="left" border="0" style="padding-top:10px;">
    <tr>
        <td id="revControlPRMHelp"  colspan="3" class="groupTitle"><%= _("Step 1 - Assign managers of paper reviewing")%></td>
    </tr>
    <tr>
        <td colspan="3">
            <% if ConfReview.getEnablePRMEmailNotif(): %>
                <div style="padding:5px; color:gray;">
                    <span class="collShowBookingsText"><%=_("An automatically generated e-mail will be sent to newly assigned Paper Review Managers.")%></span><br>
                    <span class="collShowBookingsText"><%= _("You  can  modify this from the Paper Reviewing Setup.")%></span>
                </div>
            <% end %>
        </td>
    </tr>
</table>
<table style="padding-left:20px; width:570px;">
    <tr>
        <td class="subGroupTitle"><%= _("Managers") %></td>
    </tr>
    <tr>
        <td class="questionContent" style="padding-top:5px; padding-left:3px;">
            <span><%= _("Responsibilities: Setup, assign contributions to Referees, define team competences") %></span></span>
        </td>
    </tr>
    <tr>
        <td width="80%" style="padding-top: 5px; padding-left:3px;"><div id="PRMList"></div></td>
    </tr>
</table>
<br>

<script type="text/javascript">
                        var newPRMHandler = function(userList, setResult) {
                            indicoRequest(
                                'reviewing.conference.assignTeamPRM',
                                {
                                    conference: '<%= Conference %>',
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
                                    conference: '<%= Conference %>',
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
                                <%= jsonEncode(fossilize(ConfReview.getPaperReviewManagersList())) %>,
                                true,null,
                                true, false, null, null,
                                false, false, true,
                                newPRMHandler, userListNothing, removePRMHandler);
                        $E('PRMList').set(uf.draw());
</script>