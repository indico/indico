<% from MaKaC.paperReviewing import ConferencePaperReview %>
<% from MaKaC.common.fossilize import fossilize %>


<table width="90%" align="left" border="0">
    <tbody>
    <tr>
        <td id="revControlRefereeEditorReviewerHelp"  colspan="3" class="groupTitle"  style="padding-top: 10px;">
            <%= _("Step 2 - Assign Reviewers")%>
        </td>
    </tr>
    <% if not ConfReview.hasReviewing(): %>
    <tr>
        <td style="padding-left: 25px; padding-top:10px; color:gray;">
            <span><%= _("Type of reviewing has not been chosen yet.")%></span>
        </td>
    </tr>
    <% end %>
    <% else: %>
    <tr>
        <td>
            <% if ConfReview.getEnableRefereeEmailNotif() or ConfReview.getEnableEditorEmailNotif() or ConfReview.getEnableReviewerEmailNotif(): %>
                <div style="padding:5px; color:gray;">
                    <span class="collShowBookingsText"><%=_("An automatically generated e-mail will be sent to newly assigned Reviewers.")%></span><br>
                    <span class="collShowBookingsText"><%= _("You  can  modify this from the Paper Reviewing Setup.")%></span>
                </div>
            <% end %>
        </td>
    </tr>
    <tr>
    </tbody>
</table>
<tr><td>
<table align="left" border="0" width="60%" style="padding-left:20px;">
<tbody>
<% if ConfReview.getChoice() == ConferencePaperReview.LAYOUT_REVIEWING or ConfReview.getChoice() == ConferencePaperReview.NO_REVIEWING: %>
<% pass %>
<% end %>
<% else: %>
    <tr>
        <td class="subGroupTitle"><%= _("Referees") %></td>
    </tr>
    <tr>
        <td class="questionContent" style="padding-top:5px; padding-left:3px;">
            <span><%= _("Responsibilities: Assign contributions to reviewers and give final judgement") %></span>
        </td>
    </tr>
    <tr>
        <td width="80%" style="padding-top: 5px; padding-left:3px;"><div id="RefereeList"></div></td>
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

                        var uf = new UserListField('reviewersPRUserListDiv', 'userList',
                                <%= jsonEncode(fossilize(ConfReview.getRefereesList())) %>,
                                true,null,
                                true, false, null, null,
                                false, false, true,
                                newRefereeHandler, userListNothing, removeRefereeHandler);
                        $E('RefereeList').set(uf.draw());
</script>
    <tr>
        <td class="subGroupTitle" style="padding-top:15px;"><%= _("Content Reviewers") %></td>
    </tr>
    <tr>
        <td class="questionContent" style="padding-top:5px; padding-left:3px;">
            <span><%= _("Responsibility: Judge content verification of contributions") %></span>
        </td>
    </tr>
    <tr>
        <td width="80%" style="padding-top: 5px; padding-left:3px;"><div id="ReviewerList"></div></td>
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

                        var uf = new UserListField('reviewersPRUserListDiv', 'userList',
                                <%= jsonEncode(fossilize(ConfReview.getReviewersList())) %>,
                                true,null,
                                true, false, null, null,
                                false, false, true,
                                newReviewerHandler, userListNothing, removeReviewerHandler);
                        $E('ReviewerList').set(uf.draw());
</script>
    </tr>
<% end %>
<% if ConfReview.getChoice() == ConferencePaperReview.CONTENT_REVIEWING or ConfReview.getChoice() == ConferencePaperReview.NO_REVIEWING: %>
<% pass %>
<% end %>
<% else: %>
    <tr>
        <td class="subGroupTitle" style="padding-top:15px;"><%= _("Layout Reviewers") %></td>
    </tr>
    <tr>
        <td class="questionContent" style="padding-top:5px; padding-left:3px;">
            <span><%= _("Responsibility: Judge form verification of contributions") %></span>
        </td>
    </tr>
    <tr>
        <td width="80%" style="padding-top: 5px; padding-left:3px;"><div id="EditorList"></div></td>
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
                        var uf = new UserListField('reviewersPRUserListDiv', 'userList',
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
     <em><%= _("Once this step is done you may want to assign competences for the members of the team. Please click on the next tab ") %><a href="<%=urlHandlers.UHConfModifUserCompetences.getURL(ConfReview.getConference())%>"><%= _("Competences")%></a><%= _(" to continue the process.")%></em>
        </td>
    </tr>
    </tbody>
</table>
</td></tr>
<% end %>
<br>