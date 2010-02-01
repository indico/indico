<% from MaKaC.reviewing import ConferenceReview %>
<% from MaKaC.common.PickleJar import DictPickler %>

<% if ConfReview.hasReviewing(): %>
<table width="85%%" align="center" border="0">
        <td id="revControlRefereeEditorReviewerHelp"  colspan="3" class="groupTitle"  style="padding-top: 15px; padding-bottom: 15px;">
            <%= _("Step 2: Assign Reviewers")%>
        </td>
    </tr>
    <tr>
        <td>
            <% if ConfReview.getEnableRefereeEmailNotif() or ConfReview.getEnableEditorEmailNotif() or ConfReview.getEnableReviewerEmailNotif(): %>
                <div style="padding-top: 10px; padding-bottom: 15px;">
                    <em><%=_("An automatically generated e-mail will be send to the Reviewers you will assign")%></em><br>
                    <em><%= _("You  can  modify this from the Paper Reviewing Setup")%></em>
                </div>
            <% end %>
        </td>
    </tr>
    <tr>
</table> 

<table width="83%%" align="right" border="0">
<% if ConfReview.getChoice() == 3 or ConfReview.getChoice() == 1:%>
<% pass %>
<% end %>
<% else: %>
    <tr>
        %(refereeTable)s
        <td width="80%%" style="padding-top: 15px; padding-bottom: 15px;"><div id="RefereeList"></div></td>
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
                        }
                        var removeRefereeHandler = function(user, setResult) {
                        userId = user.get('id');
                        <% for r in ConfReview.getRefereesList():%>
                            rId = '<%= r.getId()%>';
                            if(userId == rId){
                                var del = true;
                                numberContr = '<%= len(ConfReview.getJudgedContributions(r))%>';
                                if (numberContr>0){
                                    if (!(confirm('This referee has been assigned '+numberContr+' contributions. Do you want to remove the referee anyway?'))){
                                        del = false;
                                    }
                                }
                                if (del)
                                    {
	                                    indicoRequest(
			                                'reviewing.conference.removeTeamReferee',
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
                             }
                        <% end%>
                        }
                        
                        var uf = new UserListField('PluginPeopleListDiv', 'PluginPeopleList',
                                                   <%= jsonEncode(DictPickler.pickle(ConfReview.getRefereesList())) %>,
                                                   null,null,
                                                   true, false, false,
                                                   newRefereeHandler, userListNothing, removeRefereeHandler)
                        $E('RefereeList').set(uf.draw())
</script>
    <tr>
        %(reviewerTable)s
        <td width="80%%" style="padding-top: 15px; padding-bottom: 15px;"><div id="ReviewerList"></div></td>
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
                        }
                        var removeReviewerHandler = function(user, setResult) {
                        userId = user.get('id');
                        <% for r in ConfReview.getReviewersList():%>
                            rId = '<%= r.getId()%>';
                            if(userId == rId){
                                var del = true;
                                numberContr = '<%= len(ConfReview.getReviewedContributions(r))%>';
                                if (numberContr>0){
                                    if (!(confirm('This content reviewer has been assigned '+numberContr+' contributions. Do you want to remove the content reviewer anyway?'))){
                                        del = false;
                                    }
                                }
                                if (del)
                                    {
                                        indicoRequest(
		                                'reviewing.conference.removeTeamReviewer',
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
                             }
                        <% end%>
                        }
                        
                        var uf = new UserListField('PluginPeopleListDiv', 'PluginPeopleList',
                                                   <%= jsonEncode(DictPickler.pickle(ConfReview.getReviewersList())) %>,
                                                   null,null,
                                                   true, false, false,
                                                   newReviewerHandler, userListNothing, removeReviewerHandler)
                        $E('ReviewerList').set(uf.draw())
</script>
    </tr>
<% end %>   
<%if ConfReview.getChoice() == 2 or ConfReview.getChoice() == 1:%>
<% pass %>
<% end %>
<% else: %> 
    <tr>
        %(editorTable)s
        <td width="80%%" style="padding-top: 15px;"><div id="EditorList"></div></td>
    </tr>    
<script type="text/javascript">
                        var newEditorHandler = function(userList, setResult) {
                            indicoRequest(
                                'reviewing.conference.assignTeamEditor',
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
                        }
                        var removeEditorHandler = function(user, setResult) {
                        userId = user.get('id');
                        <% for r in ConfReview.getEditorsList():%>
                            rId = '<%= r.getId()%>';
                            if(userId == rId){
                                var del = true;
                                numberContr = '<%= len(ConfReview.getEditedContributions(r))%>';
                                if (numberContr>0){
                                    if (!(confirm('This layout reviewer has been assigned '+numberContr+' contributions. Do you want to remove the layout reviewer anyway?'))){
                                        del = false;
                                    }
                                }
                                if (del)
                                    {
                                        indicoRequest(
		                                'reviewing.conference.removeTeamEditor',
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
                             }
                        <% end%>
                        }
                        
                        var uf = new UserListField('PluginPeopleListDiv', 'PluginPeopleList',
                                                   <%= jsonEncode(DictPickler.pickle(ConfReview.getEditorsList())) %>,
                                                   null,null,
                                                   true, false, false,
                                                   newEditorHandler, userListNothing, removeEditorHandler)
                        $E('EditorList').set(uf.draw())
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