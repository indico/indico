<% declareTemplate(newTemplateStyle=True) %>
<% from MaKaC.reviewing import ConferencePaperReview %>
<% from MaKaC.common.fossilize import fossilize %>


<table width="85%" align="center" border="0">
    <tr>
        <td id="revControlRefereeEditorReviewerHelp"  colspan="3" class="groupTitle"  style="padding-top: 15px; padding-bottom: 15px;">
            <%= _("Step 2: Assign Reviewers")%>
        </td>
    </tr>
    <% if not ConfReview.hasReviewing(): %>
    <tr>
        <td>
            <p style="padding-left: 25px;"><font color="gray"><%= _("Type of reviewing has not been chosen yet.")%></font></p>
        </td>
    </tr>
    <% end %>
    <% else: %>
    <tr>
        <td>
            <% if ConfReview.getEnableRefereeEmailNotif() or ConfReview.getEnableEditorEmailNotif() or ConfReview.getEnableReviewerEmailNotif(): %>
                <div style="padding-top: 10px; padding-bottom: 15px;">
                    <em><%=_("An automatically generated e-mail will be sent to newly assigned Reviewers.")%></em><br>
                    <em><%= _("You  can  modify this from the Paper Reviewing Setup.")%></em>
                </div>
            <% end %>
        </td>
    </tr>
    <tr>
</table>

<table width="83%" align="right" border="0">
<% if ConfReview.getChoice() == 3 or ConfReview.getChoice() == 1:%>
<% pass %>
<% end %>
<% else: %>
    <tr>
        <td width="80%" nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Referees") %><br><span style="font-size: 8pt"><%= _("responsiblities: Assign, contributions to Reviewers, Give final judgement") %></span></span></td>
        <td width="80%" style="padding-top: 15px; padding-bottom: 15px;"><div id="RefereeList"></div></td>
    </tr>
<script type="text/javascript">

                        var newRefereeHandler = function(userList, setResult) {
                            indicoRequest(
                                'reviewing.conference.assignTeamReferee',
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

                        var removeRefereeHandler = function(user, setResult) {
                            var userId = user.get('id');
                            var del = true;
                            var contribsPerUser = [];
                            <% for r in ConfReview.getRefereesList():%>
                            contribsPerUser['<%= r.getId()%>'] = <%= len(ConfReview.getJudgedContributions(r))%>;
                            <% end %>
                            if(exists(contribsPerUser[userId])){
                                if (contribsPerUser[userId] > 0){
                                    if (!(confirm($T('This referee has been assigned ')+contribsPerUser[userId]+$T(' contributions. Do you want to remove the referee anyway?')))){
                                        del = false;
                                    }
                                }
                            }
                            if (del) {
                                indicoRequest('reviewing.conference.removeTeamReferee',
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
                            }
                        };

                        var uf = new UserListField('userListDiv', 'userList',
                                <%= jsonEncode(fossilize(ConfReview.getRefereesList())) %>,
                                true,null,
                                true, false, null, null,
                                false, false, true,
                                newRefereeHandler, userListNothing, removeRefereeHandler);
                        $E('RefereeList').set(uf.draw());
</script>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Content Reviewers") %><br><span style="font-size: 8pt"><%= _("responsibility: judge content verification of contributions") %></span></span></td>
        <td width="80%" style="padding-top: 15px; padding-bottom: 15px;"><div id="ReviewerList"></div></td>
    </tr>
<script type="text/javascript">
                        var newReviewerHandler = function(userList, setResult) {
                            indicoRequest(
                                'reviewing.conference.assignTeamReviewer',
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
                        var removeReviewerHandler = function(user, setResult) {
                            var userId = user.get('id');
                            var del = true;
                            var contribsPerUser = [];
                            <% for r in ConfReview.getReviewersList():%>
                            contribsPerUser['<%= r.getId()%>'] = <%= len(ConfReview.getReviewedContributions(r))%>;
                            <% end %>
                            if(exists(contribsPerUser[userId])){
                                if (contribsPerUser[userId] > 0){
                                    if (!(confirm($T('This content reviewer has been assigned ')+contribsPerUser[userId]+$T(' contributions. Do you want to remove the referee anyway?')))){
                                        del = false;
                                    }
                                }
                            }
                            if (del) {
                                indicoRequest('reviewing.conference.removeTeamReviewer',
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
                            }
                        };

                        var uf = new UserListField('userListDiv', 'userList',
                                <%= jsonEncode(fossilize(ConfReview.getReviewersList())) %>,
                                true,null,
                                true, false, null, null,
                                false, false, true,
                                newReviewerHandler, userListNothing, removeReviewerHandler);
                        $E('ReviewerList').set(uf.draw());
</script>
    </tr>
<% end %>
<%if ConfReview.getChoice() == 2 or ConfReview.getChoice() == 1:%>
<% pass %>
<% end %>
<% else: %>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"> <%= _("Layout Reviewers") %><br><span style="font-size: 8pt"><%= _("responsibility: judge form verification of contributions") %></span></span></td>
        <td width="80%" style="padding-top: 15px;"><div id="EditorList"></div></td>
    </tr>
<script type="text/javascript">
                        var newEditorHandler = function(userList, setResult) {
                            indicoRequest('reviewing.conference.assignTeamEditor',
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
                        var removeEditorHandler = function(user, setResult) {
                            var userId = user.get('id');
                            var del = true;
                            var contribsPerUser = [];
                            <% for r in ConfReview.getEditorsList():%>
                            contribsPerUser['<%= r.getId()%>'] = <%= len(ConfReview.getEditedContributions(r))%>;
                            <% end %>
                            if(exists(contribsPerUser[userId])){
                                if (contribsPerUser[userId] > 0){
                                    if (!(confirm($T('This layout reviewer has been assigned ')+contribsPerUser[userId]+$T(' contributions. Do you want to remove the referee anyway?')))){
                                        del = false;
                                    }
                                }
                            }
                            if (del) {
                                indicoRequest('reviewing.conference.removeTeamEditor',
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
                            }
                        };
                        var uf = new UserListField('userListDiv', 'userList',
                                                   <%= jsonEncode(fossilize(ConfReview.getEditorsList())) %>,
                                                   true,null,
                                                   true, false, null, null,
                                                   false, false, true,
                                                   newEditorHandler, userListNothing, removeEditorHandler);
                        $E('EditorList').set(uf.draw());
</script>
<% end %>

    <tr><td style="padding-top: 15px;"></td></tr>
    <tr><td colspan="5" style="padding-top: 15px;">
     <em><%= _("You can define paper reviewers competences by clicking on 'Competences'")%></em>
        </td>
    </tr>
</table>
<% end %>
<br>