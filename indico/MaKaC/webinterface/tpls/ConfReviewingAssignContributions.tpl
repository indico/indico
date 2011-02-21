<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.common.timezoneUtils import nowutc %>
<% from MaKaC.conference import ContribStatusNone %>

<% dueDateFormat = "%a %d %b %Y" %>
<% color = '' %>
<% if not ConfReview.hasReviewing(): %>
<p style="padding-left: 25px;"><font color="gray"><%= _("Type of reviewing has not been chosen yet")%></font></p>
<% end %>
<% else: %>
<% if len(Conference.getContributionListSortedById()) == 0: %>
<p style="padding-left: 25px;"><font color="gray"><%= _("There are no contributions to assign.")%></font></p>
<% end %>
<%else:%>
<table>
    <tr>
        <td align="bottom">
            <div id="showHideFilteringHelp" style="padding-top:30px; margin-left:20px;"><div id="showHideFiltering" style="display:inline"></div></div>
        </td>
        <td align="bottom" style="padding-left:10px; padding-top:27px;">
           <div><%= _("Displaying  ")%><span id="contributionsToShow" style="font-size:15px; font-weight: bold;"></span></div>
        </td>
        <td align="bottom" style="padding-top:27px;">
            <div id="totalContributions" style="display:none;"><span><%=_("  ( Total:  ")%></span><span style="font-size:15px; font-weight: bold;"><%= len(Conference.getContributionListSortedById()) %></span>
            <span><%=_(" )")%></span>
            </div>
        </td>
    </tr>
</table>
<br/>
<table id="filteringTable" class="shadowRectangle" width="95%%" align="left" style="margin-left:20px; margin-bottom: 20px;">
    <thead>
        <tr style="text-align:left;">
            <td nowrap class="titleCellFormat" style="border-bottom:1px solid #BBBBBB;">
                <%= _("types ")%><img src="<%= Config.getInstance().getSystemIconURL("checkAll") %>" alt="Select all" title="Select all" onclick="selectAll('selTypes')" style="border:none;"><img src="<%= Config.getInstance().getSystemIconURL("uncheckAll") %>" alt="Deselect all" title="Deselect all" onclick="deselectAll('selTypes')" style="border:none;">
            </td>
            <td nowrap class="titleCellFormat" style="border-bottom:1px solid #BBBBBB;">
                <%= _("sessions")%><img src="<%= Config.getInstance().getSystemIconURL("checkAll") %>" alt="Select all" title="Select all" onclick="selectAll('selSessions')" style="border:none;"><img src="<%= Config.getInstance().getSystemIconURL("uncheckAll") %>" alt="Deselect all" title="Deselect all" onclick="deselectAll('selSessions')" style="border:none;">
            </td>
            <td nowrap class="titleCellFormat" style="border-bottom:1px solid #BBBBBB;">
                <%= _("tracks")%><img src="<%= Config.getInstance().getSystemIconURL("checkAll") %>" alt="Select all" title="Select all" onclick="selectAll('selTracks')" style="border:none;"><img src="<%= Config.getInstance().getSystemIconURL("uncheckAll") %>" alt="Deselect all" title="Deselect all" onclick="deselectAll('selTracks')" style="border:none;">
            </td>
            <td nowrap class="titleCellFormat" style="border-bottom:1px solid #BBBBBB;">
                <%= _("assign status")%>
            </td>
        </tr>
    </thead>
    <tbody>
        <tr style="vertical-align:top">
            <td>
                <table cellpadding="0px" cellspacing="0px" border="0px">
                    <tr>
                        <td><input type="checkbox" id="typeShowNoValue" name="selTypes" value="not specified" checked/></td>
                        <td> --<%= _("not specified")%>--</td>
                    </tr>
                    <% for type in self._conf.getContribTypeList(): %>
                        <tr>
                            <td><input type="checkbox" name="selTypes" value="<%=type.getId()%>" checked></td>
                            <td><%= type.getName() %></td>
                        </tr>
                    <% end %>
                </table>
            </td>
            <td>
                <table cellpadding="0px" cellspacing="0px" border="0px">
                    <tr>
                        <td><input type="checkbox" id="sessionShowNoValue" name="selSessions" value="not specified" checked/></td>
                        <td> --<%= _("not specified")%>--</td>
                    </tr>
                    <% for s in self._conf.getSessionListSorted(): %>
                        <tr>
                            <td><input type="checkbox" name="selSessions" value="<%=s.getId()%>" checked></td>
                            <td><%= s.getTitle() %></td>
                        </tr>
                    <% end %>
                </table>
            </td>
            <td>
                <table cellpadding="0px" cellspacing="0px" border="0px">
                    <tr>
                        <td><input type="checkbox" id="trackShowNoValue" name="selTracks" value="not specified" checked/></td>
                        <td> --<%= _("not specified")%>--</td>
                    </tr>
                    <% for t in Conference.getTrackList(): %>
                        <tr>
                            <td><input type="checkbox" name="selTracks" value="<%=t.getId()%>" checked></td>
                            <td><%= t.getTitle() %></td>
                        </tr>
                    <% end %>
                </table>
            </td>
            <td>
                <table style="list-style-type:none">
                    <% if not IsOnlyReferee: %>
                        <tr><td><input type="checkbox" id="showWithReferee" checked/> <%= _("With Referee assigned")%></td></tr>
                    <% end %>
                    <tr><td><input type="checkbox" id="showWithEditor" checked/> <%= _("With Layout Reviewer assigned")%></td></tr>
                    <tr><td><input type="checkbox" id="showWithReviewer" checked/> <%= _("With at least 1 Content Reviewer assigned")%></td></tr>

                </table>
            </td>
        </tr>
        <tr>
            <td id="applyFilterHelp" colspan="4" style="text-align:center; padding-top:5px;">
                <input id="applyFilter" type="button" class="popUpButton" value="Apply filter"/>
            </td>
        </tr>
    </tbody>
</table>

<table class="shadowRectangleSoft" width="95%%">
    <% if not IsOnlyReferee and not (ConfReview.getChoice() == 3 or ConfReview.getChoice() == 1): %>
    <tr>
        <td><%= _("Referee")%>:</td>
        <td id="assignRefereeHelp">
            <a id="assignRefereeButton_top" class="fakeLink" style="margin-left: 15px; margin-right: 15px"><%= _("Assign")%></a>|
            <span id="assignMenu_referee_top" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''">
                <a id="assignRefereePerTrackButton_top" class="dropDownMenu fakeLink"  style="margin-left: 15px; margin-right: 15px"><%= _("Assign per ...")%>
                </a>
            </span>|
            <a id="removeRefereeButton_top" class="fakeLink"  style="margin-left: 15px; margin-right: 15px"><%= _("Remove")%></a>
        </td>
    </tr>
    <% end %>
    <%if not (ConfReview.getChoice() == 2 or ConfReview.getChoice() == 1):%>
    <tr>
        <td><%= _("Layout Reviewer")%>:</td>
        <td id="assignEditorHelp">
            <a id="assignEditorButton_top" class="fakeLink" style="margin-left: 15px; margin-right: 15px"><%= _("Assign")%></a>|
            <span id="assignMenu_editor_top" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''">
                <a id="assignEditorPerTrackButton_top" class="dropDownMenu fakeLink"  style="margin-left: 15px; margin-right: 15px"><%= _("Assign per ...")%>
                </a>
            </span>|
            <a id="removeEditorButton_top" class="fakeLink"  style="margin-left: 15px; margin-right: 15px"><%= _("Remove")%></a>
        </td>
    </tr>
    <% end %>
    <% if not (ConfReview.getChoice() == 3 or ConfReview.getChoice() == 1): %>
    <tr>
        <td><%= _("Content Reviewers")%>:</td>
        <td id="assignReviewerHelp">
            <a id="addReviewerButton_top" class="fakeLink" style="margin-left: 15px; margin-right: 15px"><%= _("Assign")%></a>|
            <span id="assignMenu_reviewer_top" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''">
                <a id="assignReviewerPerTrackButton_top" class="dropDownMenu fakeLink"  style="margin-left: 15px; margin-right: 15px"><%= _("Assign per ...")%>
                </a>
            </span>|
            <a id="removeReviewerButton_top" class="fakeLink"  style="margin-left: 15px; margin-right: 15px"><%= _("Remove")%></a>|
            <a id="removeAllReviewersButton_top" class="fakeLink"  style="margin-left: 15px; margin-right: 15px"><%= _("Remove All")%>
        </td>
    </tr>
    <% end %>
</table>
<!--  and not (ConfReview.getChoice() == 3 or ConfReview.getChoice() == 1) -->

<table style="padding-left:40px;">
        <tr>
            <td style="padding-bottom: 5px; padding-top: 5px">
                <%= _("Select:") %>
            </td>
            <td nowrap class="titleCellFormat" style="padding-bottom: 20px;  padding-top: 20px; border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF">
                 <span onclick="selectAll('selectedContributions')" align="left" style="cursor:pointer;padding-bottom:5px;color:#0B63A5;list-style-type:none;" onmouseover="this.style.color='#E25300'" onmouseout="this.style.color='#0B63A5'">
                        <%= _("All")%>
                 </span>,
                 <span onclick="deselectAll('selectedContributions')" align="left" style="cursor:pointer;padding-bottom:5px;color:#0B63A5;list-style-type:none;" onmouseover="this.style.color='#E25300'" onmouseout="this.style.color='#0B63A5'">
                        <%= _("None")%>
                 </span>
            </td>
        </tr>
</table>
<table class="Revtab" width="95%%" cellspacing="0" align="center" border="0" style="padding-left:20px; margin-bottom:1em">
<!--
    <tr>
        <td nowrap class="groupTitle" colspan=4>Contributions to judge as Referee</td>
    </tr>
-->
    <thead>
        <tr>
            <td></td>
            <td nowrap class="subGroupTitleAssignContribution" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <%= _("Id")%>
            </td>
            <td nowrap class="subGroupTitleAssignContribution" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <%= _("Title")%>
            </td>
            <td nowrap class="subGroupTitleAssignContribution" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <%= _("Type")%>
            </td>
            <td nowrap class="subGroupTitleAssignContribution" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <%= _("Track")%>
            </td>
            <td nowrap class="subGroupTitleAssignContribution" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <%= _("Session")%>
            </td>
            <!--
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
                State
            </td>
            -->
            <td nowrap class="subGroupTitleAssignContribution" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <%= _("Reviewing team")%>
            </td>
            <td nowrap class="subGroupTitleAssignContribution" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <%= _("Deadline")%>
            </td>
        </tr>
        <tr>
            <td colspan="8" style="border-bottom: 1px solid grey"></td>
        </tr>
    </thead>

   <tbody id="tablebody">
    <% for c in Conference.getContributionListSortedById(): %>
        <% rm = c.getReviewManager() %>
        <% if not isinstance(c.getStatus(), ContribStatusNone): %>
         <tr valign="top">
            <td></td>
            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <%= c.getId() %>
            </td>

            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <a href="<%= urlHandlers.UHContributionModifReviewing.getURL(c) %>">
                    <%= c.getTitle() %>
                </a>
            </td>

            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <% if c.getType(): %>
                    <%= c.getType().getName() %>
                <% end %>
            </td>

            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <% if c.getTrack(): %>
                    <%= c.getTrack().getTitle() %>
                <% end %>
            </td>

            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <% if c.getSession(): %>
                    <%= c.getSession().getTitle() %>
                <% end %>
            </td>

            <!--
            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
            <% if rm.getLastReview().getRefereeJudgement().isSubmitted(): %>
                <span style="color:green;">
                    Judged: <%= rm.getLastReview().getRefereeJudgement().getJudgement() %>
                </span>
            <% end %>
            <% else: %>
                <span style="color:red;">Not judged yet<br>
                <%= "<br>".join(rm.getLastReview().getReviewingStatus()) %>
                </span>
            <% end %>
            </td>
            -->
            <td>
                <ul>
                    <% if not (ConfReview.getChoice() == 3 or ConfReview.getChoice() == 1): %>
                    <li>
                        <em><%= _("Referee")%>:</em>
                    </li>
                    <% end %>
                    <li>
                        <em><%= _("Layout Reviewer")%>:</em>
                    </li>
                    <li>
                        <em><%= _("Content Reviewers")%>:</em>
                        <ul>
                        <% for reviewer in rm.getReviewersList() :%>
                            <li>a</li>
                        <% end %>
                        </ul>
                    </li>
                </ul>
            </td>

            <td style="border-right:5px solid #FFFFFF; border-left:5px solid #FFFFFF;">
                <% date = rm.getLastReview().getAdjustedRefereeDueDate() %>
                <% if date is None: %>
                    <%= _("Deadline not set.")%>
                <% end %>
                <% else: %>
                    <%= date.strftime(dueDateFormat) %>
                <% end %>
            </td>
        </tr>
        <% end %>
    <% end %>
    </tbody>
</table>

<table class="shadowRectangleSoft" width="95%%" style="margin-top:10px;">
    <% if not IsOnlyReferee and not (ConfReview.getChoice() == 3 or ConfReview.getChoice() == 1): %>
    <tr>
        <td><%= _("Referee")%>:</td>
        <td id="assignRefereeHelp">
            <a id="assignRefereeButton_bottom" class="fakeLink" style="margin-left: 15px; margin-right: 15px"><%= _("Assign")%></a>|
            <span id="assignMenu_referee_bottom" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''">
                <a id="assignRefereePerTrackButton_top" class="dropDownMenu fakeLink"  style="margin-left: 15px; margin-right: 15px"><%= _("Assign per ...")%>
                </a>
            </span>|
            <a id="removeRefereeButton_bottom" class="fakeLink"  style="margin-left: 15px; margin-right: 15px"><%= _("Remove")%></a>
        </td>
    </tr>
    <% end %>
    <%if not (ConfReview.getChoice() == 2 or ConfReview.getChoice() == 1):%>
    <tr>
        <td><%= _("Layout Reviewer")%>:</td>
        <td id="assignEditorHelp">
            <a id="assignEditorButton_bottom" class="fakeLink" style="margin-left: 15px; margin-right: 15px"><%= _("Assign")%></a>|
            <span id="assignMenu_editor_bottom" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''">
                <a id="assignEditorPerTrackButton_bottom" class="dropDownMenu fakeLink"  style="margin-left: 15px; margin-right: 15px"><%= _("Assign per ...")%>
                </a>
            </span>|
            <a id="removeEditorButton_bottom" class="fakeLink"  style="margin-left: 15px; margin-right: 15px"><%= _("Remove")%></a>
        </td>
    </tr>
    <% end %>
    <% if not (ConfReview.getChoice() == 3 or ConfReview.getChoice() == 1): %>
    <tr>
        <td><%= _("Content Reviewers")%>:</td>
        <td id="assignReviewerHelp">
            <a id="addReviewerButton_bottom" class="fakeLink" style="margin-left: 15px; margin-right: 15px"><%= _("Assign")%></a>|
            <span id="assignMenu_reviewer_bottom" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''">
                <a id="assignReviewerPerTrackButton_bottom" class="dropDownMenu fakeLink"  style="margin-left: 15px; margin-right: 15px"><%= _("Assign per ...")%>
                </a>
            </span>|
            <a id="removeReviewerButton_bottom" class="fakeLink"  style="margin-left: 15px; margin-right: 15px"><%= _("Remove")%></a>|
            <a id="removeAllReviewersButton_bottom" class="fakeLink"  style="margin-left: 15px; margin-right: 15px"><%= _("Remove All")%>
        </td>
    </tr>
   <% end %>
</table>

<div id="userSelection_bottom" style="margin-top: 1em">
    <span id="userSelectionMessage_bottom"></span>
    <ul id="userList_bottom">
    </ul>
</div>




<script type="text/javascript">
var assignPerTrackMenus = function(role, place){
    var assignMenu = $E('assignMenu'+'_'+role+'_'+place);
    var order = 'assign';
    if(role=='reviewer'){
       order = 'add';
    }
    assignMenu.observeClick(function(e) {
        var menuItems = {};

        menuItems[$T('Track')] = function(){ fetchUsersPerAttribute(order, role, 'track'); };
        menuItems[$T('Session')] = function(){ fetchUsersPerAttribute(order, role, 'session'); };
        menuItems[$T('Type')] = function(){ fetchUsersPerAttribute(order, role, 'type'); };

        var menu = new PopupMenu(menuItems, [assignMenu], "popupList");
        var pos = assignMenu.getAbsolutePosition();
        menu.open(pos.x, pos.y + 20);
        return false;
    });
}

var contributions = $L(); // watchlist of contribution objects, pickled from Indico Contribution objects
var contributionsIndexes = []; //array that maps contribution ids to the index of the contribution in the 'contributions' watchlist
var action = ''; // stores which button has been pressed, in order to know which list of users has to be retrieved

/**
 * Returns a contribution object given its id.
 * The contribution object is obtained from the 'contributions' watchlist.
 * @param {Object} id The id of the contribution.
 */
var getContribution = function (id) {
    return contributions.item(contributionsIndexes[id]);
}

/**
 * Selects all the checkboxes of a given name
 */
var selectAll = function (name) {
    var checkBoxes = document.getElementsByName(name);
    if ( checkBoxes ) { // true if there is at least 1 checkbox
        if ( !checkBoxes.length) { // true if there is only 1 checkbox
            checkBoxes.checked=true;
            if (checkBoxes.name == "selectedContributions") {
                isSelected(checkBoxes.id.split('b')[1]);
            }
        } else { // there is more than 1 checkbox
            for (i = 0; i < checkBoxes.length; i++) {
                checkBoxes[i].checked=true;
                if (checkBoxes[i].name == "selectedContributions") {
                    isSelected(checkBoxes[i].id.split('b')[1]);
                }
            }
        }
    }
}

/**
 * Deselects all the contributions by unticking their checkboxes
 */
var deselectAll = function(name) {
    var checkBoxes = document.getElementsByName(name)
    if ( checkBoxes ) { // true if there is at least 1 checkbox
        if ( !checkBoxes.length) { // true if there is only 1 checkbox
            checkBoxes.checked=false;
            if (checkBoxes.name == "selectedContributions") {
                isSelected(checkBoxes.id.split('b')[1]);
            }
        } else { // there is more than 1 checkbox
            for (i = 0; i < checkBoxes.length; i++) {
                checkBoxes[i].checked=false;
                if (checkBoxes[i].name == "selectedContributions") {
                    isSelected(checkBoxes[i].id.split('b')[1]);
                }
            }
        }
    }
}

/**
 * Builds the 'link' to show and hide the filtering options.
 */
var buildShowHideFiltering = function() {
    var option = new Chooser({
        showFiltering: command(function(){
            $E('filteringTable').dom.style.display = '';
            option.set('hideFiltering');
        }, $T('Show Filters')),
        hideFiltering: command(function(){
            $E('filteringTable').dom.style.display = 'none';
            option.set('showFiltering');
        }, $T('Hide Filters'))
    });
    option.set('showFiltering');

    $E('showHideFiltering').set(Widget.link(option));
}

/**
 * Builds a table row element from a contribution object, pickled from an Indico's Contribution object
 * @param {Object} contribution
 */
var backgroundColorOver = function() {
    var cbId = "cb" + this.id.split('_')[1];
    var checkbox = $E(cbId);
    if (!checkbox.dom.checked) {
        IndicoUI.Widgets.Generic.tooltip(this.style.backgroundColor='#FFF6DF');
    }
}

var backgroundColorOut = function() {
    var cbId = "cb" + this.id.split('_')[1];
    var checkbox = $E(cbId);
    if (!checkbox.dom.checked) {
        IndicoUI.Widgets.Generic.tooltip(this.style.backgroundColor='transparent');
    }
}


function isSelected(numId) {
    var rowId = "row_" + numId;
    var elem = $E(rowId);
    var checkboxId = "cb" + numId;
    var checkbox = $E(checkboxId);
    if (checkbox.dom.checked == true) {
        elem.dom.style.backgroundColor = '#CDEB8B';
    } else {
        elem.dom.style.backgroundColor = 'transparent';
    }
}



var contributionTemplate = function(contribution) {

    var row = Html.tr();
    var rowId = "row_" + contribution.id;
    row.dom.id = rowId;
    row.dom.onmouseover = backgroundColorOver;
    row.dom.onmouseout = backgroundColorOut;

    // Cell1: checkbox to select this contribution
    var cell1 = Html.td({style:{"textAlign":"center", "width":"0px"}});
    var id = ("cb" + contribution.id);
    var name = ("selectedContributions");

    /*
    //creating the checkbox IE way
    if (document.all) {
    var checkbox = document.createElement('<input name='+name+'>');
    checkbox.type = "checkbox";
    checkbox.id = id ;
    }
    //the other browsers
    else {
        var checkbox = Html.checkbox({id: id, name:name});
    }
    cell1.set(checkbox);
    //checkbox.dom.value = contribution.id; // has to be added after constructor because of IE
    */
    var checkbox = Html.input('checkbox', {id: id, name:name});//, onclick:"isSelected("+contribution.id+");"
    checkbox.dom.onclick = function () { // the function is here again in order to avoid problems with IE
        var rowId = "row_" + contribution.id;
        var elem = $E(rowId);
        var checkboxId = "cb" + contribution.id;
        var checkbox = $E(checkboxId);
        if (checkbox.dom.checked == true) {
            elem.dom.style.backgroundColor = '#CDEB8B';
        } else {
            elem.dom.style.backgroundColor = 'transparent';
        }
    };
    checkbox.dom.value = contribution.id;

    cell1.set(checkbox);

    row.append(cell1);

    // Cell2: contribution id
    var cell2 = Html.td({className:'contributionDataCell',style:{"textAlign":"center", "width":"0px"}});
    cell2.set(contribution.id)
    row.append(cell2);

    // Cell3: contribution title
    var cell3 = Html.td({className:'contributionDataCell'});
    // Sadly this hack is necessary to get the link since getURL() needs a Contribution object (from Indico, not the local one from Javascript)
    // and contributions are loaded asynchronously...
    linkString = "<%= urlHandlers.UHContributionModifReviewing.getURL() %>" + "?contribId=" + contribution.id + "&confId=<%= Conference.getId()%>"
    var link = Html.a({href: linkString});
    link.set(contribution.title);
    cell3.set(link);
    row.append(cell3);

    // Cell4: contribution type
    var cell4 = Html.td({className:'contributionDataCell',style:{"marginLeft":"5px"}});
    cell4.set(contribution.type ? contribution.type : "")
    row.append(cell4);

    // Cell5: contribution track
    var cell5 = Html.td({className:'contributionDataCell',style:{"marginLeft":"5px"}});
    cell5.set(contribution.track ? contribution.track : "")
    row.append(cell5);

    // Cell6: contribution session
    var cell6 = Html.td({className:'contributionDataCell',style:{"marginLeft":"5px"}});
    cell6.set(contribution.session ? contribution.session : "")
    row.append(cell6);

    /*
    // Cell7: contribution status
    var cell7 = Html.td();

    if (contribution.reviewManager.lastReview.refereeJudgement.isSubmitted) {
        var span = Html.span();
        span.dom.style.color = 'green';
        span.set("Judged" + contribution.reviewManager.lastReview.refereeJudgement.judgement);
        cell7.set(span);

    } else {
        var ul = Html.ul();
        ul.dom.style.color = 'red';
        ul.dom.style.listStyleType = 'none';
        ul.dom.style.padding = 0;
        ul.dom.style.marginLeft = '5px';

        var li = Html.li();
        li.set("Not judged yet");
        ul.append(li);

        statusList = contribution.reviewManager.lastReview.reviewingStatus;
        for (j in statusList) {
            var li = Html.li();
            li.set(statusList[j])
            ul.append(li)
        }

        cell7.set(ul);
    }

    row.append(cell7);
    */

    // Cell8: reviewing team assigned to the contribution
    var cell8 = Html.td({className:'contributionDataCell'});

    var ul = Html.ul();
    ul.dom.style.listStyleType = 'none';
    ul.dom.style.padding = 0;
    ul.dom.style.marginLeft = '5px';

    <% if not (ConfReview.getChoice() == 3 or ConfReview.getChoice() == 1): %>
    var li1 = Html.li();
    var span1 = Html.span({}, $T('Referee: '))
    var span2 = contribution.reviewManager.referee ?
                    Html.span({id: ("creferee" + contribution.id), style:{"fontWeight":"bolder"}},  contribution.reviewManager.referee) :
                    Html.span({id: ("creferee" + contribution.id)},$T('No referee'));
    li1.set(Widget.block([span1,span2]));
    ul.append(li1);
    <% end %>

    <% if not (ConfReview.getChoice() == 2 or ConfReview.getChoice() == 1): %>
    var li2 = Html.li();
    var span1 = Html.span({}, $T('Layout reviewer: '))
    var span2 = contribution.reviewManager.editor ?
                    Html.span({id: ("ceditor" + contribution.id), style:{"fontWeight":"bolder"}},  contribution.reviewManager.editor) :
                    Html.span({id: ("ceditor" + contribution.id)},$T('No layout reviewer'));
    li2.set(Widget.block([span1,span2]));
    ul.append(li2);
    <% end %>

    <% if not (ConfReview.getChoice() == 3 or ConfReview.getChoice() == 1): %>
    var li3 = Html.li();
    var span = Html.span({id : ("creviewerstitle" + contribution.id)}, $T('Content reviewers: '));
    li3.append(span);


    var ulReviewers = Html.ul();
    if (contribution.reviewManager.reviewersList.length > 0){
        for (j in contribution.reviewManager.reviewersList) {
            var li = Html.li({id: ("creviewer" + contribution.id + "_" + contribution.reviewManager.reviewersList[j].id), style:{"fontWeight":"bolder"}});
            li.set(contribution.reviewManager.reviewersList[j].name);
            ulReviewers.append(li);
        }
        li3.append(ulReviewers);
    } else {
        var span = Html.span({id: ("creviewer" + contribution.id)},$T('No content reviewers' ));
        li3.append(span);
    }
    ul.append(li3);
    <% end %>

    cell8.set(ul);
    row.append(cell8);

    // Cell9: due date of the contribution
    var cell9 = Html.td({className:'contributionDataCell'});
    if (contribution.reviewManager.lastReview.refereeDueDate == null) {
        cell9.set("");
    }
    else {
        var date = contribution.reviewManager.lastReview.refereeDueDate.date;
        var newDate = date.split('-')[2] + '-' + date.split('-')[1] + '-' + date.split('-')[0];
        cell9.set(newDate);
    }
    row.append(cell9);

    return row;
}


/**
 * Updates the display of the contribution row.
 * @param {Object} id The id of the contribution.
 */
var updateContribution = function (id) {
    index = contributionsIndexes[id];
    var c = contributions.item(index);
    contributions.removeAt(index);
    contributions.insert(c, index);
}


/**
 * Returns a list of checkbox values, for a given checkbox name
 * ('name' attribute of an 'input' HTML element)
 * The list only contains the checkboxes who are selected.
 * The first checkbox ('--not specified--' one) is discarded.
 * @param {Object} checkboxName
 */
var getCheckedBoxes = function(checkboxName) {

    var checkBoxes = document.getElementsByName(checkboxName);
    var checkedIds = []
    for (var i=0; i<checkBoxes.length; i++) {
        var cb = checkBoxes[i];
        if (cb.checked && cb.value != "not specified") {
            checkedIds.push(cb.value)
        }
    }
    return checkedIds;
}


/**
 * Returns a list of contribution ids.
 * Only the contributios whose checkbox has been selected are returned.
 */
var getCheckedContributions = function() {

    var checkBoxes = document.getElementsByName('selectedContributions');
    var checkedContributions = []

    for (var i=0; i<checkBoxes.length; i++) {
        var cb = checkBoxes[i];
        if (cb.checked) {
            checkedContributions.push(cb.id.slice(2))
        }
    }
    return checkedContributions;
}

/**
 * Turns the given user orange for some seconds to indicate that it has changed
 * @param {Object} contributionId The id of the contribution where a user has been assigned
 * @param {Object} role The role that has been assigned
 * @param {Object} reviewerId In case of a reviewerm the reviewerId. Otherwise leave to null.
 */
var colorify = function(contributionId, role, reviewerId) {
    id = "c" + role + contributionId;
    if (reviewerId) {
        id = id + "_" + reviewerId;
    }
    IndicoUI.Effect.highLight(id, 'orange', 2000);
}

/**
 * Among a list of contributions (given as contribution ids),
 * this function unchecks the checboxes of the contributions
 * who don't ahve a refree yet.
 * @param {array} contributions List of contribution ids
 */
var deselectWithoutReferee = function(contributions) {
    for (i in contributions) {
        contributionId = contributions[i];
        contribution = getContribution(contributionId);
        if (contribution.reviewManager.referee == null) {
            $E('cb' + contributionId).dom.checked = false;
            isSelected(contributionId);
        }
    }
}

/**
 * Among a list of contributions (given as contribution ids),
 * this function unchecks the checboxes of the contributions
 * who don't have a reviewer.
 * @param {array} contributions List of contribution ids
 */
var deselectWithoutReviewer = function(contributions) {
    for (i in contributions) {
        contributionId = contributions[i];
        contribution = getContribution(contributionId);
        if (contribution.reviewManager.reviewersList.length == 0) {
            $E('cb' + contributionId).dom.checked = false;
            isSelected(contributionId);
        }
    }
}

/**
 * Checks that all contributions have a Referee.
 * Returns true if all have a referee, false otherwise.
 * If none have a referee, an alert message appear.
 * If some have a referee and others don't, a dialog will appear offering
 * the choice to only apply the assignment to contributions with referee.
 * @param {Object} contributions
 * @param {Object} order
 * @param {Object} role
 */
var checkAllHaveReferee = function(contributions, order, role, assignPerAttribute) {
    var contributionsWithoutReferee = []
    for (i in contributions) {
        contributionId = contributions[i]
        contribution = getContribution(contributionId)
        if (contribution.reviewManager.referee == null) {
            contributionsWithoutReferee.push(contributionId)
        }
    }
    if (contributionsWithoutReferee.length == contributions.length) {
        alert($T("None of the contributions you checked have a Referee.") +
            $T("You can only add a layout reviewer or a content reviewer if the contribution has a referee.")
        );
        return false;
    }

    if (contributionsWithoutReferee.length > 0) {

        if(assignPerAttribute){
            alert($T("Some of the contributions you checked have a Referee.") +
            $T("You can only add a layout reviewer or a content reviewer if the contribution has a referee."));
            return false;
        } else {
        title =$T('Contributions without referee');

        var popup = new ExclusivePopup(title, function(){popup.close();});

        popup.draw = function(){

            var span1 = Html.span({}, $T("Some of the contributions you checked do not have a Referee."));
            var span2 = Html.span({}, $T("You can only add an editor or a reviewer if the contribution has a referee."));
            var span3 = Html.span({}, $T("Do you want to add that " + role + " only to the contributions with a referee?"));
            var yesButton = Html.button('popUpButton', $T("Yes"));
            yesButton.observeClick(function(){
                deselectWithoutReferee(contributions);
                fetchUsers(order, role);
                popup.close();
            });

             var noButton = Html.button('popUpButton', $T("No"));
            noButton.observeClick(function(){
                popup.close();
            });
              var buttons = Widget.inline([yesButton, noButton])
              var all = Widget.lines([span1, span2, span3, buttons])
         return this.ExclusivePopup.prototype.draw.call(this, Html.div({style: {height: '130px', width: '420px'}},[all]));
                };
             popup.open();

        return false;
    }
    }
    return true;
}

/**
 * When removing a reviewer from one or more contributions this function takes care for the alert messages.
 * Returns true if there are no warnings, returns false otherwise.
 * If are checked contributions with no reviewers assigned, an alert message appears.
 * If some have a reviewers and others don't, a dialog will appear offering
 * the choice to only apply the assignment to contributions with reviewer.
 * @param {Object} contributions
 * @param {Object} order
 * @param {Object} role
 */
var removeReviewersAlerts = function(contributions, role) {
    contributionsWithoutReviewers = []
    for (i in contributions) {
        contributionId = contributions[i]
        contribution = getContribution(contributionId)
        if (contribution.reviewManager.reviewersList.length == 0) {
            contributionsWithoutReviewers.push(contributionId)
        }
    }
    if (contributionsWithoutReviewers.length == contributions.length) {
        alert($T("There is no assigned Content Reviewer to remove.")
        );
        return false;
    }

    /*contributionsWithoutEditor = []
    for (i in contributions) {
        contributionId = contributions[i]
        contribution = getContribution(contributionId)
        if (contribution.reviewManager.editor = null) {
            contributionsWithoutEditor.push(contributionId)
        }
    }

    if (contributionsWithoutEditor.length == contributions.length) {
        alert($T("There is no assigned Layout Reviewer to remove.")
        );
        return false;
    } */

    if (contributionsWithoutReviewers.length > 0) {
        title =$T('Contributions without reviewer');

        var popup = new ExclusivePopup(title, function(){popup.close();});

        popup.draw = function(){

            var span1 = Html.span({}, $T("The Content Reviewers will be removed only from the contributions that have one."));
            var okButton = Html.button('popUpButton', $T("OK"));
            okButton.observeClick(function(){
                deselectWithoutReviewer(contributions);
                removeUser('allReviewers');
                popup.close();
            });

              var all = Widget.lines([span1, okButton])
              okButton.dom.align = 'center';
              return this.ExclusivePopup.prototype.draw.call(this, Html.div({style: {height: '100px', width: '250px'}},[all]));
                };
             popup.open();

        return false;
    }

    return true;
}

var removeEditorAlerts = function(contributions, role) {

    contributionsWithoutEditor = []
    for (i in contributions) {
        contributionId = contributions[i]
        contribution = getContribution(contributionId)
        if (contribution.reviewManager.editor == null) {
            contributionsWithoutEditor.push(contributionId)
        }
    }

    if (contributionsWithoutEditor.length == contributions.length) {
        alert($T("There is no assigned Layout Reviewer to remove.")
        );
        return false;
    }

    return true;

}

var removeNoRefereeAlerts = function(contributions, role) {

    contributionsWithoutEditor = []
    for (i in contributions) {
        contributionId = contributions[i]
        contribution = getContribution(contributionId)
        if (contribution.reviewManager.referee == null) {
            contributionsWithoutEditor.push(contributionId)
        }
    }

    if (contributionsWithoutEditor.length == contributions.length) {
        alert($T("There is no assigned Referee to remove.")
        );
        return false;
    }

    return true;

}

/**
 * When removing a refereee from one or more contributions this function checks
 * if there are alredy assigned reviewers or editor, or both
 * @param {array} contributions List of contribution ids
 */
var removeRefereeAlerts = function(contributions){
    for (i in contributions) {
        contributionId = contributions[i]
        contribution = getContribution(contributionId)
    }
    if(contribution.reviewManager.reviewersList.length != 0 && contribution.reviewManager.editor != null) {
            return false;
        }
    if(contribution.reviewManager.reviewersList.length != 0 && contribution.reviewManager.editor == null){
           return false;
        }
    if(contribution.reviewManager.reviewersList.length == 0 && contribution.reviewManager.editor != null) {
            return false;
        }

    return true;
}

/**
 * When removing a refereee from one or more contributions this function takes care for the alert messages.
 * If are checked contributions with alredy assigned reviewers/editor
 * alert message appears that a referee should be assigned
 * @param {array} contributions List of contribution ids
 */
var removeRefereeAlertsMessage = function(contributions){
    for (i in contributions) {
        contributionId = contributions[i]
        contribution = getContribution(contributionId)
    }
    var warning = $T("You have to assign new referee.")
    var message = $T("")
    if(contribution.reviewManager.reviewersList.length != 0 && contribution.reviewManager.editor != null) {
            message = $T("Please note that layout and content have already been assigned for this/these contributions."+ warning)
            return message;
        }
    if(contribution.reviewManager.reviewersList.length != 0 && contribution.reviewManager.editor == null){
           message = $T("Please note that a content reviewer has already been assigned for this/these contributions."+ warning)
           return message;
        }
    if(contribution.reviewManager.reviewersList.length == 0 && contribution.reviewManager.editor != null) {
           message = $T("Please note that a layout reviewer has already been assigned for this/these contributions."+ warning)
            return message;
        }

    return message;
}

/**
 * Function that is called when a user (referee, editor, reviewer) is clicked.
 * Depending on what has been sotred in the variable 'action', the user will be
 * added as a referee, added as an editor, removed as a reviewer, etc on the checked contributions.
 * @param {Object} user The user that has been clicked.
 */
var userSelected = function(user, contrPerAttribute){

    var checkedContributions = getCheckedContributions()


    if (checkedContributions.length > 0){
        var params = {conference: '<%= Conference.getId() %>',contributions: checkedContributions, user: user.id}
      }


    if(checkedContributions.length == 0 && contrPerAttribute.length > 0){
        var params = {conference: '<%= Conference.getId() %>',contributions: contrPerAttribute, user: user.id}
        var checkedContributions = contrPerAttribute;
    }

    if (checkedContributions.length > 0 || (checkedContributions.length == 0 && contrPerAttribute.length > 0)) {



        switch(action) {
        case 'assign_referee':
        	var killProgress = IndicoUI.Dialogs.Util.progress();
            indicoRequest(
                'reviewing.conference.assignReferee',
                params,
                function(result,error) {
                    if (!error) {
                        for (i in checkedContributions) {
                            contributionId = checkedContributions[i];
                            contribution = getContribution(contributionId);
                            contribution.reviewManager.referee = user.name;
                            updateContribution(contributionId);
                            colorify(contributionId,'referee');
                            $E('cb' + contributionId).dom.checked = true; //updateContribution will build a row with an unchecked checkbox
                            isSelected(contributionId);
                        }
                        killProgress();
                    } else {
                    	killProgress();
                        IndicoUtil.errorReport(error);
                    }
                }
            );
            break;

        case 'assign_editor':
        	var killProgress = IndicoUI.Dialogs.Util.progress();
            indicoRequest(
                'reviewing.conference.assignEditor',
                params,
                function(result,error) {
                    if (!error) {
                        for (i in checkedContributions) {
                            contributionId = checkedContributions[i]
                            contribution = getContribution(contributionId)
                            contribution.reviewManager.editor = user.name
                            updateContribution(contributionId)
                            colorify(contributionId,'editor');
                            $E('cb' + contributionId).dom.checked = true; //updateContribution will build a row with an unchecked checkbox
                            isSelected(contributionId);
                        }
                        killProgress();
                    } else {
                    	killProgress();
                        IndicoUtil.errorReport(error);
                    }
                }
            );
            break;

        case 'add_reviewer':
        	var killProgress = IndicoUI.Dialogs.Util.progress();
            indicoRequest(
                'reviewing.conference.addReviewer',
                params,
                function(result,error) {
                    if (!error) {
                        for (i in checkedContributions) {
                            contributionId = checkedContributions[i]
                            contribution = getContribution(contributionId)

                            var present = false;
                            for (j in contribution.reviewManager.reviewersList) {
                                if (contribution.reviewManager.reviewersList[j].id == user.id) {
                                    present = true;
                                    break;
                                }
                            }
                            if (!present) {
                                contribution.reviewManager.reviewersList.push(user)
                            }

                            updateContribution(contributionId);
                            colorify(contributionId,'reviewer', user.id);
                            $E('cb' + contributionId).dom.checked = true; //updateContribution will build a row with an unchecked checkbox
                            isSelected(contributionId);
                        }
                        killProgress();
                    } else {
                    	killProgress();
                        IndicoUtil.errorReport(error);
                    }
                }
            );
            break;

        case 'remove_reviewer':
            indicoRequest(
                'reviewing.conference.removeReviewer',
                params,
                function(result, error) {
                    notinlist2 = [];
                    if(!error) {
                        for (i in checkedContributions) {
                            contributionId = checkedContributions[i]
                            contribution = getContribution(contributionId)

                            notinlist = false;
                            deleted = false;
                            for (j in contribution.reviewManager.reviewersList) {
                                if (contribution.reviewManager.reviewersList[j].id == user.id) {
                                    contribution.reviewManager.reviewersList.splice(j,1);
                                    updateContribution(contributionId);
                                    colorify(contributionId,'reviewerstitle');
                                    $E('cb' + contributionId).dom.checked = true; //updateContribution will build a row with an unchecked checkbox
                                    isSelected(contributionId);
                                    deleted = true;
                                } else {
                                    notinlist = true;
                                    notinlist2.push(contributionId)
                                    $E('cb' + contributionId).dom.checked = false;
                                    isSelected(contributionId);
                                }
                            }
                        }
                   } else {
                        IndicoUtil.errorReport(error);
                   }
                }
            );
            break;

        default:
            break;
        }

    }
}



/**
 * Requests the list of contribution from the server,
 * given the filtering parameters.
 */
var fetchContributions = function() {

    contributions.clear();
    contributionsIndexes = []
    indicoRequest('event.contributions.list',
        {
            conference: '<%= Conference.getId() %>',
            typeShowNoValue : $E('typeShowNoValue').dom.checked,
            trackShowNoValue : $E('trackShowNoValue').dom.checked,
            sessionShowNoValue : $E('sessionShowNoValue').dom.checked,
            selTypes : getCheckedBoxes('selTypes'),
            selTracks : getCheckedBoxes('selTracks'),
            selSessions : getCheckedBoxes('selSessions'),
            <% if not IsOnlyReferee: %>
            showWithReferee: $E('showWithReferee').dom.checked,
            <% end %>
            showWithEditor: $E('showWithEditor').dom.checked,
            showWithReviewer: $E('showWithReviewer').dom.checked
        },
        function(result, error){
            if (!error) {
                for (i in result) {
                    c = result[i]
                    contributions.append(c);
                    contributionsIndexes[c.id] = i;
                }
                $E('contributionsToShow').dom.innerHTML = result.length;
                var totalContributions = <%= len(Conference.getContributionListSortedById()) %>;
                if (totalContributions == result.length) {
                    $E('totalContributions').dom.style.display = 'none';
                } else {
                    $E('totalContributions').dom.style.display = '';
                }
            } else {
                IndicoUtil.errorReport(error);
            }
        }
    )
}

/**
 * Retrieves a list of users from the server.
 * @param {string} order The action that will be taken on the users: 'assign', 'remove'.
 * @param {string} role The role of the users: 'referee', 'editor', 'reviewer'.
 */
var fetchUsers = function(order, role) {

    var checkedContributions = getCheckedContributions();
    if (checkedContributions.length == 0) {
        alert($T("Please select at least 1 contribution"));
        return;
    }

    if ((order == 'assign' && role == 'editor') || (order == 'add' && role == 'reviewer')) {
        <% if not (ConfReview.getChoice() == 3 or ConfReview.getChoice() == 1): %>
            if (!checkAllHaveReferee(checkedContributions, order, role, false)) {
                return;
            }
        <% end %>
   }

   if (order == 'remove' && role == 'reviewer')  {
        if (!removeReviewersAlerts(checkedContributions, role)) {
            return;
        }
   }


    indicoRequest(
        'reviewing.conference.userCompetencesList',
        {conference: '<%= Conference.getId() %>', role: role},
        function(result,error) {
            if (!error) {

                action = order + '_' + role;

                var title = '';
                var new_assign = '';
                if (role == 'editor') {
                    title = $T('Click on a user name to ') + order + $T(' a layout reviewer:');
                }
                if (role == 'reviewer') {
                    title = $T('Click on a user name to ') + order + ' a ' + $T('content reviewer:');
                } else {
                    if (order == 'assign') {
                    title = $T('Click on a user name to ') + order + ' a ' + role + ':';
                    } if(order == 'new_assign' && !removeRefereeAlerts(checkedContributions)) {
                        action = 'assign_' + role;
                        title = $T('Click on a user name to assign new ') + role + ':';
                        new_assign = 'True';
                    }
                }

                var popup = new ExclusivePopup(title, function(){popup.close();});

                popup.draw = function(){
                        var users = $L();
                        var userTemplate = function(user) {
                            var li = Html.li();
                            var userName = Widget.link(command(function(){
                                userSelected(user);
                                var killProgress = IndicoUI.Dialogs.Util.progress()
                                popup.close();
                                killProgress();
                            }, user.name));


                        var userCompetences = Html.span({style:{marginLeft:'5px'}},
                            user.competences.length == 0 ? $T('(no competences defined)') : $T('(competences: ') + user.competences.join(', ') + ')'
                        );

                        li.set(Widget.inline([userName, userCompetences]));
                        return li;
                    }

                        var userList = Html.ul();
                        bind.element(userList, users, userTemplate);

                        for (i in result) {
                        users.append(result[i]);
                        }

                        var cancelButton = Html.button({style:{marginLeft:pixels(5)}}, $T("Cancel"));
                          cancelButton.observeClick(function(){
                          popup.close();
                           });

                       var span1 = Html.span({}, "");
                       var message = '';
                       if(new_assign) {
                            span1 = Html.span({}, removeRefereeAlertsMessage(checkedContributions));
                       }
                       if(role == 'reviewer' && order == 'remove') {
                            if (checkedContributions.length == 1){
                                    message = $T("The Reviewer you choose will be removed only from the contribution that is assigned to him/her.")
                                } else {
                                    message = $T("The Reviewer you choose will be removed only from the contributions that are assigned to him/her.")
                                }
                            span1 = Html.span({}, message);
                       }
                        return this.ExclusivePopup.prototype.draw.call(this, Widget.block([span1, userList, cancelButton]));
                };
             popup.open();

            } else {
                IndicoUtil.errorReport(error);
            }
        }
    );
}

var fetchUsersPerAttribute = function(order, role, attribute) {

    var checkedContributions = getCheckedContributions();
    if (checkedContributions.length > 0) {
        deselectAll('selectedContributions');
    }


    indicoRequest(
        'reviewing.conference.userCompetencesList',
        {conference: '<%= Conference.getId() %>', role: role},
        function(result,error) {
            if (!error) {

                action = order + '_' + role;

                var title = '';
                if (role == 'editor') {
                    title = $T('Follow the steps to ') + order + $T(' a layout reviewer:');
                }
                if (role == 'reviewer') {
                    title = $T('Follow the steps to ') + order + $T(' a content reviewer:');
                }
                if (role == 'referee') {
                    title = $T('Follow the steps to ') + order + ' a ' + role + ':';
                }

                var popup = new ExclusivePopup(title, function(){popup.close();});

                popup.draw = function(){

                     var AttributeDiv = Html.div();

                     var attributeList = function () {
                        indicoRequest(
                        'reviewing.conference.attributeList',
                        {conference: '<%= Conference.getId()%>', attribute: attribute},
                        function(result, error){
                            if(!error){
                                    var attributes = $L();
                                    var attributeTemplate = function(att){
		                                var li = Html.li({style:{listStyleType:"none", paddingBottom:'3px'}});
		                                var id = (att.id);
		                                var name = ("selected"+attribute);
		                                var checkbox = Html.input('checkbox', {id: id, name: name});
		                                var attributeName = Html.span({style:{marginLeft:'5px', fontSize: '13px'}}, att.title);

		                                li.set(Widget.inline([checkbox, attributeName]));

		                                return li;
                                    }
	                                var step1 = Html.span({style:{fontSize:'18px'}, className:'groupTitle groupTitleNoBorder'}, 'Step 1: Choose a '+ attribute);
	                                var attList = Html.ul();
	                                bind.element(attList, attributes, attributeTemplate);
                                    if(result.length==0) {
                                        var killProgress = IndicoUI.Dialogs.Util.progress()
                                        popup.close();
                                        killProgress();
                                        alert('There is no '+attribute+' define.');
                                    }
	                                for (i in result) {
	                                attributes.append(result[i]);
	                                }

                                    AttributeDiv.set(Widget.block([step1,attList]));
                            } else {
                                    IndicoUtil.errorReport(error);
                            }
                        }
                        );
                     }

                     var getCheckedAttributes = function() {
                            var checkBoxes = document.getElementsByName("selected"+attribute);
                            var checkedAttributes = []
                            for (var i=0; i<checkBoxes.length; i++) {
                                var cb = checkBoxes[i];
                                if (cb.checked) {
                                    checkedAttributes.push(cb.id)
                                }
                            }
                            return checkedAttributes;
                     }
                     var assignButton = Html.button({style:{marginLeft:pixels(5)}}, $T("Assign"));

                     var users = $L();
                     var contrPerAttribute = [];

                     var contributionsIdList = function (user, chAtt){
                                    indicoRequest(
                                        'reviewing.conference.contributionsIdPerSelectedAttribute',
                                        {conference: '<%= Conference.getId()%>', attribute: attribute, selectedAttributes:chAtt },
                                        function(result, error){
                                            if(!error){
                                                    for (i in result) {
                                                          contrPerAttribute.push(result[i]);
                                                    }
                                                    if ((order == 'assign' && role == 'editor') || (order == 'add' && role == 'reviewer')) {
													        <% if not (ConfReview.getChoice() == 3 or ConfReview.getChoice() == 1): %>
													            if (!checkAllHaveReferee(contrPerAttribute, order, role, true)) {
													                return;
													            }
													        <% end %>
													   }
                                                    userSelected(user, contrPerAttribute);
                                            }
                                            else {
                                                IndicoUtil.errorReport(error);
                                            }
                                        }
                                   );
                                }
                     var userTemplate = function(user) {
                            var li = Html.li({style:{listStyleType:"none", paddingBottom:'3px'}});
                            var name = ("radioBtn");
                            var radioButton = Html.input('radio', {id: user.id, name: name});
                            var userName = Html.label({style:{fontWeight: 'normal'}}, user.name);

                            var userCompetences = Html.span({style:{marginLeft:'5px', fontSize: '11px'}},
                                user.competences.length == 0 ? $T('(no competences defined)') : $T('(competences: ') + user.competences.join(', ') + ')'
                            );

                            li.set(Widget.inline([radioButton, userName, userCompetences]));
                            return li;
                     }
                     var step2 = Html.span({style:{fontSize:'18px'}, className:'groupTitle groupTitleNoBorder'}, 'Step 2: Click on a user name to assign a '+ role);
                     var userList = Html.ul();
                     bind.element(userList, users, userTemplate);

                     for (i in result) {
                        users.append(result[i]);
                     }

                     attributeList();

                     assignButton.observeClick(function(){
                                var chAtt = getCheckedAttributes();
                                if(chAtt.length == 0){
                                    alert($T('You must select at least one attribute.'));
                                } else {
	                                var checkedBtn = function(){
		                                var allBtn = document.getElementsByName('radioBtn');
			                            for (var i=0; i<allBtn.length; i++) {
			                                var cb = allBtn[i];
			                                if (cb.checked) {
			                                   return cb.id
			                                }
			                            }
		                           }
		                           var checkedBtnId = checkedBtn();
		                           if(checkedBtnId == null){
		                               alert($T('You must select at least one user.'));
		                           } else {
									   for (var i=0; i < users.length.get(); i++) {
									       user = users.item(i);
									       if (user.id == checkedBtnId) {
									           contributionsIdList(user, chAtt);
									       }
									   }
		                               var killProgress = IndicoUI.Dialogs.Util.progress()
		                               popup.close();
		                               killProgress();
	                               }
                                }
                            });

                     var cancelButton = Html.button({style:{marginLeft:pixels(5)}}, $T("Cancel"));
                          cancelButton.observeClick(function(){
                          popup.close();
                     });

                     return this.ExclusivePopup.prototype.draw.call(this, Html.div({style: {height: 'auto', width: 'auto'}},Widget.block([AttributeDiv, step2, userList, assignButton, cancelButton])));
                };
              popup.open();

              } else {
                  IndicoUtil.errorReport(error);
              }
        }
    );
}

/**
 * Removes the referee, the editor, or all the reviewers from the contributions that are selected.
 * @param {Object} role 'referee', 'editor', 'allReviewers'
 */
var removeUser = function(role) {

    var checkedContributions = getCheckedContributions();
    if (checkedContributions.length == 0) {
        alert($T("Please select at least 1 contribution"));
        return;
    }

    var params = {conference: '<%= Conference.getId() %>',contributions: checkedContributions}

    switch(role) {
    case 'referee':
        indicoRequest(
            'reviewing.conference.removeReferee',
            params,
            function(result,error) {
                if (!error) {
                    if (!removeNoRefereeAlerts(checkedContributions, role)) {
                                return;
                        }
                    for (i in checkedContributions) {
                        contributionId = checkedContributions[i];
                        contribution = getContribution(contributionId);
                        contribution.reviewManager.referee = null;
                        updateContribution(contributionId);
                        colorify(contributionId, 'referee')
                        $E('cb' + contributionId).dom.checked = true; //updateContribution will build a row with an unchecked checkbox
                        isSelected(contributionId);
                    }
                    if(!removeRefereeAlerts(checkedContributions)){
                      fetchUsers('new_assign', 'referee')
                    }
                } else {
                    IndicoUtil.errorReport(error);
                }
            }
        );
        break;
    case 'editor':
        indicoRequest(
            'reviewing.conference.removeEditor',
            params,
            function(result,error) {
                if (!error) {
                    if (!removeEditorAlerts(checkedContributions, role)) {
                                return;
                        }
                    for (i in checkedContributions) {
                        contributionId = checkedContributions[i];
                        contribution = getContribution(contributionId);
                        contribution.reviewManager.editor = null;
                        updateContribution(contributionId);
                        colorify(contributionId, 'editor')
                        $E('cb' + contributionId).dom.checked = true; //updateContribution will build a row with an unchecked checkbox
                        isSelected(contributionId);
                    }
                } else {
                    IndicoUtil.errorReport(error);
                }
            }
        );
        break;
    case 'allReviewers':
        indicoRequest(
            'reviewing.conference.removeAllReviewers',
            params,
            function(result,error) {
                if (!error) {
                    if (!removeReviewersAlerts(checkedContributions, role)) {
                                return;
                        }
                    for (i in checkedContributions) {
                        contributionId = checkedContributions[i];
                        contribution = getContribution(contributionId);
                        contribution.reviewManager.reviewersList = [];
                        updateContribution(contributionId);
                        colorify(contributionId, 'reviewer')
                        $E('cb' + contributionId).dom.checked = true; //updateContribution will build a row with an unchecked checkbox
                        isSelected(contributionId);
                    }
                } else {
                    IndicoUtil.errorReport(error);
                }
            }
        );
    default:
        break;
    }
}

// Code to be executed on page load

buildShowHideFiltering();
$E('filteringTable').dom.style.display = 'none';

bind.element($E("tablebody"), contributions, contributionTemplate);

$E('applyFilter').observeClick(fetchContributions);

<% if not IsOnlyReferee and not (ConfReview.getChoice() == 3 or ConfReview.getChoice() == 1): %>
$E('assignRefereeButton_top').observeClick(function(){ fetchUsers('assign', 'referee'); });
assignPerTrackMenus('referee', 'top');
assignPerTrackMenus('referee', 'bottom');
$E('assignRefereeButton_bottom').observeClick(function(){ fetchUsers('assign', 'referee'); });
$E('removeRefereeButton_top').observeClick(function(){ removeUser('referee') });
$E('removeRefereeButton_bottom').observeClick(function(){ removeUser('referee') });
<% end %>

<% if not (ConfReview.getChoice() == 2 or ConfReview.getChoice() == 1): %>
$E('assignEditorButton_top').observeClick(function(){ fetchUsers('assign', 'editor'); });
assignPerTrackMenus('editor', 'top');
assignPerTrackMenus('editor', 'bottom');
$E('assignEditorButton_bottom').observeClick(function(){ fetchUsers('assign', 'editor'); });
$E('removeEditorButton_top').observeClick(function(){ removeUser('editor') });
$E('removeEditorButton_bottom').observeClick(function(){ removeUser('editor') });
<% end %>

<% if not (ConfReview.getChoice() == 3 or ConfReview.getChoice() == 1): %>
$E('addReviewerButton_top').observeClick(function(){ fetchUsers('add', 'reviewer'); });
assignPerTrackMenus('reviewer', 'top');
assignPerTrackMenus('reviewer', 'bottom');
$E('addReviewerButton_bottom').observeClick(function(){ fetchUsers('add', 'reviewer'); });
$E('removeReviewerButton_top').observeClick(function(){ fetchUsers('remove', 'reviewer'); });
$E('removeReviewerButton_bottom').observeClick(function(){ fetchUsers('remove', 'reviewer'); });
$E('removeAllReviewersButton_top').observeClick(function(){ removeUser('allReviewers') });
$E('removeAllReviewersButton_bottom').observeClick(function(){ removeUser('allReviewers') });
<% end %>

fetchContributions();

</script>
<% end %>
<% end %>
