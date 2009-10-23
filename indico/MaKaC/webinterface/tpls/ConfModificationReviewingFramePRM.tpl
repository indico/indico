<% from MaKaC.reviewing import ConferenceReview %>
<% from MaKaC.common.PickleJar import DictPickler %>

<% if not ConfReview.hasReviewing(): %>
<table align="center"><tr><td><%= _("Type of reviewing has not been chosen yet")%></td></tr></table>
<% end %>
<%else:%>
<br>
<table width="85%%" align="center" border="0">
    <tr>
        <em><%= _("Please, follow the steps to assign Paper Reviewing Team")%></em> 
        <td id="revControlPRMHelp"  colspan="3" class="groupTitle" style="border: none; padding-top: 15px;"><%= _("Step 1: Assign Managers of Paper Reviewing Module")%></td>
    </tr>
    <tr>
         <td style="padding-top: 15px;">%(paperReviewManagerTable)s</td>
        <td width="80%%" style="padding-top: 15px;"><div id="PRMList"></div></td>
    </tr>
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
                        }
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
                        }
                        
                        var uf = new UserListField('PluginPeopleListDiv', 'PluginPeopleList',
                                                   <%= jsonEncode(DictPickler.pickle(ConfReview.getPaperReviewManagersList())) %>,
                                                   null,null,
                                                   true, false, false,
                                                   newPRMHandler, userListNothing, removePRMHandler)
                        $E('PRMList').set(uf.draw())
</script>
<% end %>