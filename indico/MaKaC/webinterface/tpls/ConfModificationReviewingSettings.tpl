<% declareTemplate(newTemplateStyle=True) %>

<% from MaKaC.reviewing import ConferenceReview %>
<% from MaKaC.reviewing import Template %>
<% from MaKaC.common.utils import formatDateTime %>

<table width="90%%" align="center" border="0" style="border-left: 1px solid #777777; margin-bottom:1em">
    <tr>
        <td id="reviewingModeHelp" colspan="5" class="groupTitle">
            <span><%= _("Choose type of paper reviewing for the conference")%></span>
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD">
            <span class="titleCellFormat"><%= _("Type of reviewing")%></span>
        </td>
        <td nowrap style="vertical-align:top">
            <span id="inPlaceEditReviewingMode" style="display:inline"><%= ConferenceReview.reviewingModes[choice] %></span>
        </td>
    </tr>
</table>

<% if ConfReview.hasReviewing(): %>
    <% display = 'table' %>
<% end %>
<% else: %>
    <% display = 'none' %>
<% end %>
<table id='materialsTable' width="90%%" align="center" border="0" style="border-left: 1px solid #777777; margin-bottom:1em; display:<%=display%>">
    <tr>
        <td id="reviewableMaterialsHelp" colspan="5" class="groupTitle">
            <span><%= _("Choose types of materials to be revised")%></span>
        </td>
    </tr>
    <tr>
        <td>
            <div id="inPlaceEditReviewableMaterials"><%=", ".join(ConfReview.getReviewableMaterials()) %></div>
        </td>
    </tr>
</table>

<% if ConfReview.hasPaperReviewing(): %>
    <% display = 'table' %>
<% end %>
<% else: %>
    <% display = 'none' %>
<% end %>
<table id='statusTable' width="90%%" align="center" border="0" style="border-left: 1px solid #777777; margin-bottom:1em; display:<%=display%>">
    <tr>
        <td id="reviewingStatesHelp" colspan="5" class="groupTitle"><%= _("Add a paper status for paper reviewing")%></td>
    </tr>
    <!--
    <tr>
    <form action=<%=addStateURL%> method="post">
        <%= stateAdd %>
    </form>
    </tr>
    <tr>
        <form action=<%=removeStateURL%> method="post">
            <td bgcolor="white" width="50%%" valign="top" class="blacktext">
                <%= stateTable %>
            </td>
            
        </form>
    </tr>
    -->
    <tr>
        <td>
            <div id="inPlaceEditStates"><%= ', '.join(ConfReview.getAllStates())%></div>
        </td>
    </tr>
</table>

<% if ConfReview.hasPaperReviewing(): %>
    <% display = 'table' %>
<% end %>
<% else: %>
    <% display = 'none' %>
<% end %>
<table id="reviewingQuestionsTable" width="90%%" align="center" border="0" style="border-left: 1px solid #777777; margin-bottom:1em; display:<%=display%>">
    <tr>
        <td id="reviewingQuestionsHelp" colspan="5" class="groupTitle"><%= _("Add questions for paper reviewing")%></td>
    </tr>
    <!--
    <tr>
        <form action=<%=addQuestionURL%> method="post">
            <%= questionAdd %>
        </form>
    </tr>
    <tr>
        <form action=<%=removeQuestionURL%> method="post">
          <td bgcolor="white" width="50%%" valign="top" class="blacktext">
              <%= questionTable%>
          </td>
        </form>
    </tr>
    -->
    <tr>
        <td>
            <div id="inPlaceEditQuestions"><%= ', '.join(ConfReview.getReviewingQuestions())%></div>
        </td>
    </tr>
</table>


<% if ConfReview.hasPaperEditing(): %>
    <% display = 'table' %>
<% end %>
<% else: %>
    <% display = 'none' %>
<% end %>
<table id="editingCriteriaTable" width="90%%" align="center" border="0" style="border-left: 1px solid #777777; margin-bottom:1em; display:<%=display%>">
    <tr>
        <td id="editingCriteriaHelp" colspan="5" class="groupTitle"><%= _("Set criteria for paper editing")%></td>
    </tr>
    <!--
    <tr>
        <form action=<%=addCriteriaURL%> method="post">
            <%= criteriaAdd %>
            </form>
    </tr>
    <tr>
        <form action=<%=removeCriteriaURL%> method="post">
        <td bgcolor="white" width="50%%" valign="top" class="blacktext">
             <%= criteriaTable %>
        </td>
        </form>
    </tr>
    -->
    <tr>
        <td>
            <div id="inPlaceEditCriteria"><%= ', '.join(ConfReview.getLayoutCriteria())%></div>
        </td>
    </tr>
</table>


<% if ConfReview.hasReviewing(): %>
    <% display = 'table' %>
<% end %>
<% else: %>
    <% display = 'none' %>
<% end %>
<table id="defaultDueDatesTable" width="90%%" align="center" border="0" style="border-left: 1px solid #777777; margin-bottom:1em; display:<%=display%>">
    <tr>
        <td id="defaultDatesHelp" colspan="5" class="groupTitle"><%= _("Default due dates for reviewing team")%></td>
    </tr>
    <% if ConfReview.hasPaperReviewing(): %>
        <% display = 'table-row' %>
    <% end %>
    <% else: %>
        <% display = 'none' %>
    <% end %>    
    <tr id="refereeDefaultDateRow" style="white-space:nowrap; display: <%=display%>">
        <td nowrap class="titleCellTD"><span class="titleCellFormat">
            <%= _("Referee default due date")%>
        </span></td>
        <td nowrap class="blacktext">
            <span id="inPlaceEditDefaultRefereeDueDate">
                <% date = ConfReview.getAdjustedDefaultRefereeDueDate() %>
                <% if date is None: %>
                    <%= _("Date has not been set yet.")%>
                <% end %>
                <% else: %>
                    <%= formatDateTime(date) %>
                <% end %>
            </span>
        </td>
    </tr>
    <% if ConfReview.hasPaperEditing(): %>
        <% display = 'table-row' %>
    <% end %>
    <% else: %>
        <% display = 'none' %>
    <% end %>    
    <tr id="editorDefaultDateRow" style="white-space:nowrap; display: <%=display%>">
        <td nowrap class="titleCellTD"><span class="titleCellFormat">
            <%= _("Editor default due date")%>
        </span></td>
        <td nowrap class="blacktext">
            <span id="inPlaceEditDefaultEditorDueDate">
                <% date = ConfReview.getAdjustedDefaultEditorDueDate() %>
                <% if date is None: %>
                    <%= _("Date has not been set yet.")%>
                <% end %>
                <% else: %>
                    <%= formatDateTime(date) %>
                <% end %>
            </span>
        </td>
        <% if not ConfReview.hasPaperReviewing(): %>
            <% display = 'table-row' %>
        <% end %>
        <% else: %>
            <% display = 'none' %>
        <% end %>   
    </tr>
    <% if ConfReview.hasPaperReviewing(): %>
        <% display = 'table-row' %>
    <% end %>
    <% else: %>
        <% display = 'none' %>
    <% end %>    
    <tr id="reviewerDefaultDateRow" style="white-space:nowrap;display: <%=display%>">
        <td nowrap class="titleCellTD"><span class="titleCellFormat">
            <%= _("Reviewer default due date")%>
        </span></td>
        <td nowrap class="blacktext">
            <span id="inPlaceEditDefaultReviewerDueDate">
                <% date = ConfReview.getAdjustedDefaultReviewerDueDate() %>
                <% if date is None: %>
                    <%= _("Date has not been set yet.")%>
                <% end %>
                <% else: %>
                    <%= formatDateTime(date) %>
                <% end %>
            </span>
        </td>
    </tr>
</table>


<% if ConfReview.hasReviewing(): %>
    <% display = 'table' %>
<% end %>
<% else: %>
    <% display = 'none' %>
<% end %>
<table id="templateTable" width="90%%" align="center" border="0" style="border-left: 1px solid #777777; display:<%=display%>">
    <tr>
        <td id="uploadTemplateHelp" colspan="5" class="groupTitle"><%= _("Upload a template")%></td>
    </tr>
    <tr>
        <td>
<form action="<%= setTemplateURL %>" method="post" ENCTYPE="multipart/form-data">
            <table>
            	<tr>
            		<td align="right">
            			Name
            		</td>
					<td>
						<input type=text size="70" name="name">
					</td>
            	</tr>
                <tr>
                    <td align="right">
                        <%= _("Description")%>
                    </td>
                    <td>
                        <input type=text size="70" name="description">
                    </td>
                </tr>
                <tr>
                    <td align="right">
                        <%= _("Format")%>
                    </td>
                    <td>
                        <select name="format">
                        	<option value="Unknown"><%= _("--Select a format--")%></option>
                            <% for f in Template.formats: %>
						    <option value="<%= f %>"><%= f %></option>
							<% end %>
                        </select>
                        or <input name="formatOther" size="25" value="">
                    </td>
                </tr>
				<tr>
                    <td align="right">
                        Template
                    </td>
                    <td>
                        <input name="file" type="file" value="<%= _("Browse...")%>">
                    </td>
                </tr>
            </table>
        </td>
    </tr>
    <tr>
        <td>
            <input type="submit" class="btn" value="<%= _("Upload")%>">
        </td>
</form>
    </tr>
    <tr><td>
        <% includeTpl ('ContributionReviewingTemplatesList', ConfReview = ConfReview, CanDelete = CanDelete)%>
    </tr></td>
</table>


<script type="text/javascript">
                    
var observer = function(value) {
    
    if (value == "No reviewing") {
        $E('materialsTable').dom.style.display = 'none';
        $E('statusTable').dom.style.display = 'none';
        $E('reviewingQuestionsTable').dom.style.display = 'none';
        $E('editingCriteriaTable').dom.style.display = 'none';
        $E('defaultDueDatesTable').dom.style.display = 'none';
        $E('refereeDefaultDateRow').dom.style.display = 'none';
        $E('editorDefaultDateRow').dom.style.display = 'none';
        $E('reviewerDefaultDateRow').dom.style.display = 'none';
        $E('templateTable').dom.style.display = 'none';
    }
    if (value == "Paper reviewing") {
        $E('materialsTable').dom.style.display = '';
        $E('statusTable').dom.style.display = '';
        $E('reviewingQuestionsTable').dom.style.display = '';
        $E('editingCriteriaTable').dom.style.display = 'none';
        $E('defaultDueDatesTable').dom.style.display = '';
        $E('refereeDefaultDateRow').dom.style.display = '';
        $E('editorDefaultDateRow').dom.style.display = 'none';
        $E('reviewerDefaultDateRow').dom.style.display = '';
        $E('templateTable').dom.style.display = '';
        
        showReviewableMaterials();
        showReviewingStates();
        showReviewingQuestions();
        showDefaultReviewerDate();
        showDefaultRefereeDate();
    }
    if (value == "Paper editing") {
        $E('materialsTable').dom.style.display = '';
        $E('statusTable').dom.style.display = 'none';
        $E('reviewingQuestionsTable').dom.style.display = 'none';
        $E('editingCriteriaTable').dom.style.display = '';
        $E('defaultDueDatesTable').dom.style.display = '';
        $E('refereeDefaultDateRow').dom.style.display = 'none';
        $E('editorDefaultDateRow').dom.style.display = '';
        $E('reviewerDefaultDateRow').dom.style.display = 'none';
        $E('templateTable').dom.style.display = '';
        
        showReviewableMaterials();
        showEditingCriteria();
        showDefaultEditorDate();
    }
    if (value == "Paper editing and reviewing") {
        $E('materialsTable').dom.style.display = '';
        $E('statusTable').dom.style.display = '';
        $E('reviewingQuestionsTable').dom.style.display = '';
        $E('editingCriteriaTable').dom.style.display = '';
        $E('defaultDueDatesTable').dom.style.display = '';
        $E('refereeDefaultDateRow').dom.style.display = '';
        $E('editorDefaultDateRow').dom.style.display = '';
        $E('reviewerDefaultDateRow').dom.style.display = '';
        $E('templateTable').dom.style.display = '';
        
        showReviewableMaterials();
        showReviewingStates();
        showReviewingQuestions();
        showDefaultReviewerDate();
        showDefaultRefereeDate();
        showEditingCriteria();
        showDefaultEditorDate();
    }
}

new IndicoUI.Widgets.Generic.selectionField($E('inPlaceEditReviewingMode'),
                    'reviewing.conference.changeReviewingMode',
                    {conference: '<%= ConfReview.getConference().getId() %>'},
                    <%= ConferenceReview.reviewingModes[1:] %>,
                    "<%= ConfReview.getReviewingMode() %>",
                    observer);
                    
var showReviewableMaterials = function() {
    new IndicoUI.Widgets.Generic.twoListField($E('inPlaceEditReviewableMaterials'),
                        10,"200px",<%=ConfReview.getNonReviewableMaterials()%>,<%=ConfReview.getReviewableMaterials()%>,
                        "Non reviewable materials", "Reviewable materials",
                        'reviewing.conference.changeReviewableMaterials',
                        {conference: '<%= ConfReview.getConference().getId() %>'},
                        '');
}
                    
var showReviewingStates = function() {
    new IndicoUI.Widgets.Generic.keywordField(
        $E('inPlaceEditStates'),
        'multipleLinesListItem',
        'reviewing.conference.changeStates',
        {conference: '<%= ConfReview.getConference().getId() %>'}
    );
}

var showReviewingQuestions = function() {
    new IndicoUI.Widgets.Generic.keywordField(
        $E('inPlaceEditQuestions'),
        'multipleLinesListItem',
        'reviewing.conference.changeQuestions',
        {conference: '<%= ConfReview.getConference().getId() %>'}
    );
}

var showEditingCriteria = function() {
    new IndicoUI.Widgets.Generic.keywordField(
        $E('inPlaceEditCriteria'),
        'multipleLinesListItem',
        'reviewing.conference.changeCriteria',
        {conference: '<%= ConfReview.getConference().getId() %>'}
    );
}

var showDefaultRefereeDate = function() {
    new IndicoUI.Widgets.Generic.dateEditor($E('inPlaceEditDefaultRefereeDueDate'),
                       'reviewing.conference.changeDefaultDueDate',
                       {conference: '<%= ConfReview.getConference().getId() %>',
                        dueDateToChange: 'Referee'},
                       null, true);
}
               
var showDefaultEditorDate = function() {
    new IndicoUI.Widgets.Generic.dateEditor($E('inPlaceEditDefaultEditorDueDate'),
                       'reviewing.conference.changeDefaultDueDate',
                       {conference: '<%= ConfReview.getConference().getId() %>',
                        dueDateToChange: 'Editor'},
                       null, true);
}

var showDefaultReviewerDate = function() {
    new IndicoUI.Widgets.Generic.dateEditor($E('inPlaceEditDefaultReviewerDueDate'),
                       'reviewing.conference.changeDefaultDueDate',
                       {conference: '<%= ConfReview.getConference().getId() %>',
                        dueDateToChange: 'Reviewer'},
                       null, true);
}
                       
<% if ConfReview.hasReviewing(): %>
    showReviewableMaterials();
<% end %>
<% if ConfReview.hasPaperReviewing(): %>
    showReviewingStates();
    showReviewingQuestions();
    showDefaultReviewerDate();
    showDefaultRefereeDate();
<% end %>
<% if ConfReview.hasPaperEditing(): %>
    showEditingCriteria();
    showDefaultEditorDate();
<% end %>

</script>