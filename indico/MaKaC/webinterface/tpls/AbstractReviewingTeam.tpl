<% declareTemplate(newTemplateStyle=True) %>
<% from MaKaC.common.fossilize import fossilize %>
<table width="90%" align="left" border="0" style="padding-top:10px;">
    <tr>
        <td id="revControlPRMHelp"  colspan="3" class="groupTitle"><%= _("Assign reviewers by track")%></td>
    </tr>
    <tr>
        <td colspan="3">
            <div style="padding:5px; color:gray;">
                <% if tracks: %>
                    <span class="collShowBookingsText"><%=_("Note that the reviewers will be track coordinators of that track.")%></span>
                <% end %>
                <% else: %>
                    <span class="collShowBookingsText"><%=_("There are no tracks created yet")%></span>
                <% end %>
            </div>
        </td>
    </tr>
</table>
<table width="50%" align="left">
<% for track in tracks: %>
    <tr>
        <td>
            <table width="50%" align="left" style="padding-left:20px; padding-bottom:15px; width:500px;">
                <tr>
                    <td class="subGroupTitle"><%= track.getTitle() %></td>
                </tr>
                <tr>
                    <td width="80%" style="padding-top: 5px; padding-left:3px;"><div id="track_<%=track.getId()%>"></div></td>
                </tr>
            </table>
        </td>
    </tr>
<% end %>
</table>

<script type="text/javascript">

var trackIds = <%= trackIds %>;

var listOfAddHandlers = {};

<% for i in trackIds: %>
    // set the track id
    trackId = 'track_'+ '<%= i %>';

    // Create the handlers
    var addReviewerHandler = function(user, setResult) {
        indicoRequest(
                'abstractReviewing.team.addReviewer',
                {
                    conference: '<%= conf %>',
                    track: '<%= i %>',
                    user: user[0]['id']
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
    	indicoRequest(
                'abstractReviewing.team.removeReviewer',
                {
                    conference: '<%= conf %>',
                    track: '<%= i %>',
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

    // Create the component for each track
    var uf = new UserListField('reviewersPRUserListDiv', 'userList',
            <%= jsonEncode(fossilize(coordinatorsByTrack[i])) %>,
            true,null,
            true, false, null, null,
            false, false, true,
            addReviewerHandler, null, removeReviewerHandler);



    // Draw the component
    $E(trackId).set(uf.draw());

<% end %>

</script>

