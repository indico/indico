<% declareTemplate(newTemplateStyle=True) %>

<% from MaKaC.reviewing import ConferenceReview %>
<% from MaKaC.reviewing import Template %>
<% from MaKaC.common.utils import formatDateTime %>
<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% import MaKaC.common.Configuration as Configuration %>
<table width="90%%" border="0" style="margin-bottom:1em">
    <tr>
        <td nowrap id="reviewingModeHelp" class="groupTitle"><%= _("Step 1: Choose type of paper reviewing for the conference")%>
        </td>
    </tr>
        <em><%= _("Please, follow the steps to set up the Paper Reviewing Module")%></em> 
</table>
        
<table width="90%%" border="0" style="margin-bottom:1em">
    <tr>
        <td>
        
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"  style="padding-top: 5px;">
            <span class="titleCellFormat"><%= _("Type of reviewing:")%></span>
        </td>
        <td nowrap style="vertical-align:top; padding-top: 5px;">
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
<table id='steptitle' width="90%%" border="0" style="margin-bottom:1em; display:<%=display%>">
    <tr>
        <td class="groupTitle">
            <%= _("Step 2: Set up the options for ")%><span id="title">
            <%if ConferenceReview.reviewingModes[choice]==ConferenceReview.reviewingModes[2]: %><%= _("content reviewing team")%><% end %>
            <%if ConferenceReview.reviewingModes[choice]==ConferenceReview.reviewingModes[3]: %><%= _("layout reviewing team")%><% end %>
            <%if ConferenceReview.reviewingModes[choice]==ConferenceReview.reviewingModes[4]: %><%= _("content and layout reviewing team")%><% end %>
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
<!-- for now we leave the boxes for chosing reviewing material not to display(they are not used any more)
ToDo: to remove the code which is not using any more, but to know that we have this wonderful Widget  -->
<table id='materialsTable' width="90%%" align="center" border="0" style="display:none;">
    <tr>
        <td id="reviewableMaterialsHelp" colspan="5" class="reviewingsubtitle" style="padding-top: 20px;">
            <span><%= _("Choose types of materials to be revised")%></span>
        </td>
    </tr>
    <tr>
        <td>
           <div id="inPlaceEditReviewableMaterials"  style="padding-top: 5px;"><%=", ".join(ConfReview.getReviewableMaterials()) %></div> 
        </td>
    </tr>
</table>

<% if ConfReview.hasPaperReviewing(): %>
    <% display = 'table' %>
<% end %>
<% else: %>
    <% display = 'none' %>
<% end %>
<table id='statusTable' width="90%%" align="center" border="0" style="margin-bottom:1em; display:<%=display%>">
    <tr>
        <td id="reviewingStatesHelp" colspan="5" class="reviewingsubtitle"><%= _("Add a paper status for paper reviewing")%></td>
    </tr>
    <tr>
        
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
        <td style="width: 400px;">  
            <div class="titleCellFormat" style="padding-top: 5px;">
                <%= _("The default statuses are: ")%><em><%= _("Accept, To be corrected")%></em><%=_(" and ")%><em><%=_("Reject")%></em>.<%= _(" You can define your own statuses")%>
            </div>
            <div id="inPlaceEditStates"  style="padding-top: 10px;"><%= ', '.join(ConfReview.getAllStates())%></div>
        </td>
    </tr>
</table>

<% if ConfReview.hasPaperReviewing(): %>
    <% display = 'table' %>
<% end %>
<% else: %>
    <% display = 'none' %>
<% end %>
<table id="reviewingQuestionsTable" width="90%%" align="center" border="0" style="margin-bottom:1em; display:<%=display%>">
    <tr>
        <td id="reviewingQuestionsHelp" colspan="5" class="reviewingsubtitle"><%= _("Add questions for content reviewing")%></td>
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
            <div id="inPlaceEditQuestions"  style="padding-top: 5px;"><%= ', '.join(ConfReview.getReviewingQuestions())%></div>
        </td>
    </tr>
</table>


<% if ConfReview.hasPaperEditing(): %>
    <% display = 'table' %>
<% end %>
<% else: %>
    <% display = 'none' %>
<% end %>
<table id="editingCriteriaTable" width="90%%" align="center" border="0" style="margin-bottom:1em; display:<%=display%>">
    <tr>
        <td id="editingCriteriaHelp" colspan="5" class="reviewingsubtitle"  style="padding-top: 5px;"><%= _("Set criteria for layout reviewing")%></td>
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
            <div id="inPlaceEditCriteria"  style="padding-top: 10px;"><%= ', '.join(ConfReview.getLayoutCriteria())%></div>
        </td>
    </tr>
</table>


<% if ConfReview.hasReviewing(): %>
    <% display = 'table' %>
<% end %>
<% else: %>
    <% display = 'none' %>
<% end %>
<table id="defaultDueDatesTable" width="90%%" align="center" border="0" style="margin-bottom:1em; display:<%=display%>">
    <tr>
        <td id="defaultDatesHelp" colspan="5" class="reviewingsubtitle"><%= _("Deadlines for reviewing team")%></td>
    </tr>
    <% if ConfReview.hasPaperReviewing(): %>
        <% display = 'table-row' %>
    <% end %>
    <% else: %>
        <% display = 'none' %>
    <% end %>    
    <tr id="refereeDefaultDateRow" style="white-space:nowrap; display: <%=display%>">
        <td nowrap class="titleCellTD" style="text-align:left"><span class="titleCellFormat" align="left">
            <%= _("Referee Deadline")%>
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
        <td nowrap class="titleCellTD" style="text-align:left"><span class="titleCellFormat">
            <%= _("Layout Reviewer Deadline")%>
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
        <td nowrap class="titleCellTD" style="text-align:left"><span class="titleCellFormat">
            <%= _("Content Reviewer Deadline")%>
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

<table id="automaticNotification" width="90%%" align="center" border="0">
    <% if ConfReview.hasReviewing(): %>
            <% display = 'table' %>
        <% end %>
        <% else: %>
            <% display = 'none' %>
        <% end %>
	    <tr id="autoEmails" style="display:<%=display%>">
	        <td id="automaticNotificationHelp" colspan="5" class="reviewingsubtitle"><%= _("Automatic e-mails")%>
	           <% inlineContextHelp(_('Here you can enable/disable automatic e-mails sending.<br/>Notifications can be send to the Reviewing Team in the next several situations<br/><ul><li>when are added/removed Reviewers for the conference</li><li>when are assinged/removed contributions to Reviewers</li><li>when authors of the contributions have been submitted materials</li></ul>Notifications can be send to the authors when their contributions had been judged by the Reviewers.'))%>
	        </td>
	    </tr>
        <% if ConfReview.hasPaperReviewing(): %>
            <% display = 'table-row' %>
        <% end %>
        <% else: %>
            <% display = 'none' %>
        <% end %>
	   <tr id="refereeNotif" style="white-space:nowrap; display: <%=display%>">
	    <td>
            <div>
                <span id="refereeNotifButton">                    
                </span>
            </div>
        </td>
       </tr>
        <% if ConfReview.hasPaperEditing(): %>
            <% display = 'table-row' %>
        <% end %>
        <% else: %>
            <% display = 'none' %>
        <% end %>
       <tr id="editorNotif" style="white-space:nowrap; display: <%=display%>">
          <td>
            <div>
                <span id="editorNotifButton">                    
                </span>
            </div>
         </td>
       </tr>
        <% if ConfReview.hasPaperReviewing(): %>
            <% display = 'table-row' %>
        <% end %>
        <% else: %>
            <% display = 'none' %>
        <% end %>
       <tr id="reviewerNotif" style="white-space:nowrap; display: <%=display%>">
        <td>
            <div>
                <span id="reviewerNotifButton">                   
                </span>
            </div>
        </td>
       </tr>
       <% if ConfReview.hasPaperReviewing(): %>
            <% display = 'table-row' %>
        <% end %>
        <% else: %>
            <% display = 'none' %>
        <% end %>
       <tr id="refereeNotifForContribution" style="white-space:nowrap; display: <%=display%>">
        <td>
            <div>
                <span id="refereeNotifForContributionButton">                    
                </span>
            </div>
        </td>
       </tr>
        <% if ConfReview.hasPaperEditing(): %>
            <% display = 'table-row' %>
        <% end %>
        <% else: %>
            <% display = 'none' %>
        <% end %>
       <tr id="editorNotifForContribution" style="white-space:nowrap; display: <%=display%>">
          <td>
            <div>
                <span id="editorNotifForContributionButton">                    
                </span>
            </div>
         </td>
       </tr>
        <% if ConfReview.hasPaperReviewing(): %>
            <% display = 'table-row' %>
        <% end %>
        <% else: %>
            <% display = 'none' %>
        <% end %>
       <tr id="reviewerNotifForContribution" style="white-space:nowrap; display: <%=display%>">
        <td>
            <div>
                <span id="reviewerNotifForContributionButton">                   
                </span>
            </div>
        </td>
       </tr>
       <% if ConfReview.hasPaperReviewing(): %>
            <% display = 'table-row' %>
        <% end %>
        <% else: %>
            <% display = 'none' %>
        <% end %>
       <tr id="authorSubmittedMatRefereeNotif" style="white-space:nowrap; display: <%=display%>">
        <td>
            <div>
                <span id="authorSubmittedMatRefereeNotifButton">                    
                </span>
            </div>
        </td>
       </tr>
        <% if ConfReview.hasPaperEditing(): %>
            <% display = 'table-row' %>
        <% end %>
        <% else: %>
            <% display = 'none' %>
        <% end %>
       <tr id="authorSubmittedMatEditorNotif" style="white-space:nowrap; display: <%=display%>">
          <td>
            <div>
                <span id="authorSubmittedMatEditorNotifButton">                    
                </span>
            </div>
         </td>
       </tr>
        <% if ConfReview.hasPaperReviewing(): %>
            <% display = 'table-row' %>
        <% end %>
        <% else: %>
            <% display = 'none' %>
        <% end %>
       <tr id="authorSubmittedMatReviewerNotif" style="white-space:nowrap; display: <%=display%>">
        <td>
            <div>
                <span id="authorSubmittedMatReviewerNotifButton">                   
                </span>
            </div>
        </td>
       </tr>
       <% if ConfReview.hasPaperReviewing(): %>
            <% display = 'table-row' %>
        <% end %>
        <% else: %>
            <% display = 'none' %>
        <% end %>
       <tr id="refereeJudgementNotif" style="white-space:nowrap; display: <%=display%>">
        <td>
            <div>
                <span id="refereeJudgementNotifButton">                    
                </span>
            </div>
        </td>
       </tr>
        <% if ConfReview.hasPaperEditing(): %>
            <% display = 'table-row' %>
        <% end %>
        <% else: %>
            <% display = 'none' %>
        <% end %>
       <tr id="editorJudgementNotif" style="white-space:nowrap; display: <%=display%>">
          <td>
            <div>
                <span id="editorJudgementNotifButton">                    
                </span>
            </div>
         </td>
       </tr>
        <% if ConfReview.hasPaperReviewing(): %>
            <% display = 'table-row' %>
        <% end %>
        <% else: %>
            <% display = 'none' %>
        <% end %>
       <tr id="reviewerJudgementNotif" style="white-space:nowrap; display: <%=display%>">
        <td>
            <div>
                <span id="reviewerJudgementNotifButton">                   
                </span>
            </div>
        </td>
       </tr>
</table>

<% if ConfReview.hasReviewing(): %>
    <% display = 'table' %>
<% end %>
<% else: %>
    <% display = 'none' %>
<% end %>
<form action="<%= setTemplateURL %>" method="post" ENCTYPE="multipart/form-data">
<table id="templateTable" width="90%%" align="center" border="0" style="display:<%=display%>">
    <tr>
        <td id="uploadTemplateHelp" colspan="5" class="reviewingsubtitle"><%= _("Upload a template")%></td>
    </tr>
   <!--  <tr>
        <td>
            <table>
            	<tr>
            		<td align="right">
            			<%= _("Name")%>
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
                        <textarea rows="2" cols="53" name="description">
                    </td>
                </tr>
                <tr>
                    <td align="right">
                        <%= _("Format")%>
                    </td>
                    <td id='formatchooser'>                        
                    </td>
                    
                </tr>
				<tr>
                    <td align="right">
                        <%= _("Template")%>
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
    </tr> --> 
    <tr><a name="UploadTemplate" />
        <td style="padding-left: 15px;" ><input id='uploadTpl' type="button" value="<%= _('Upload Template')%>"></a>                        
        </td>
    </tr>
    <tr><td>
        <% if ConfReview.hasTemplates(): %>
         <% display = 'table' %>
       <% end %>
       <% else: %>
         <% display = 'none' %>
       <% end %>
    <table id="templateListTableAll" width="90%%" align="center" border="0" style="display:<%=display%>">
    <!-- here to put table for the uploaded templates info :) -->
     <thead>
        <tr>
            <td nowrap width="50%%" class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #DDDDDD;">
                <%= _("Name")%>
            </td>
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #DDDDDD;">
                <%= _("Format")%>
            </td>
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #DDDDDD;">
                <%= _("Description")%>
            </td>
        </tr>
        </thead>
        <tbody id="templateListTable">
        </tbody>
        <!-- <% keys = ConfReview.getTemplates().keys() %>
       <% keys.sort() %> 
        <% for k in keys: %>
            <% t = ConfReview.getTemplates()[k] %>
        <tr id="TemplateRow_<%= k %>">
            <td id="TemplateName_<%= k %>" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <a style="color:#5FA5D4" href="<%= urlHandlers.UHDownloadContributionTemplate.getURL(t) %>">
                    <%= t.getName() %>
                </a>
                <% if CanDelete: %>
                &nbsp;&nbsp;&nbsp;
                <a href="<%= urlHandlers.UHDeleteContributionTemplate.getURL(t) %>"> 
                <a href="#" onclick="deleteTemplate('<%=t.getId()%>', '<%= t.getName() %>',  '<%= k %>')"> 
                    <img class="imglink" style="vertical-align: bottom; width: 15px; height: 15px;" src="<%= Configuration.Config.getInstance().getSystemIconURL("remove") %>" alt="delete template">
                </a>
                <% end %>
            </td>
            <td id="TemplateFormat_<%= k %>" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <%= t.getFormat() %>
            </td>
            <td id="TemplateDescription_<%= k %>" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <%= t.getDescription() %>
            </td>
        </tr>
        <% end %> -->
        </table>
        <% if ConfReview.hasTemplates(): %>
         <% display = 'none' %>
       <% end %>
       <% else: %>
         <% display = 'table' %>
       <% end %>
        <table id="NoTemplateTable" width="90%%" align="center" border="0" style="display:<%=display%>">
        <tr><td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
            <%= _("No templates have been uploaded yet.")%>
        </td></tr>
        </table>
    </tr></td>
    <tr><td style="padding-bottom:15px;"></td></tr>
        <tr><td colspan="5" style="padding-top: 20px;">
            <em><%= _("To assign team for Paper Review Module, please click on 'Team' and follow the steps")%></em>
        </td></tr>    
</table>
</form>

<script type="text/javascript">

var observer = function(value) {
    
    if (value == "No reviewing") {
        $E('steptitle').dom.style.display = 'none';
        $E('title').dom.style.display = 'none';
        $E('materialsTable').dom.style.display = 'none';
        $E('statusTable').dom.style.display = 'none';
        $E('reviewingQuestionsTable').dom.style.display = 'none';
        $E('editingCriteriaTable').dom.style.display = 'none';
        $E('defaultDueDatesTable').dom.style.display = 'none';
        $E('refereeDefaultDateRow').dom.style.display = 'none';
        $E('editorDefaultDateRow').dom.style.display = 'none';
        $E('reviewerDefaultDateRow').dom.style.display = 'none';
        $E('autoEmails').dom.style.display = 'none';
        $E('refereeNotif').dom.style.display = 'none';
        $E('editorNotif').dom.style.display = 'none';
        $E('reviewerNotif').dom.style.display = 'none';
        $E('refereeNotifForContribution').dom.style.display = 'none';
        $E('editorNotifForContribution').dom.style.display = 'none';
        $E('reviewerNotifForContribution').dom.style.display = 'none';
        $E('refereeJudgementNotif').dom.style.display = 'none';
        $E('editorJudgementNotif').dom.style.display = 'none';
        $E('reviewerJudgementNotif').dom.style.display = 'none';
        $E('authorSubmittedMatRefereeNotif').dom.style.display = 'none';
        $E('authorSubmittedMatEditorNotif').dom.style.display = 'none';
        $E('authorSubmittedMatReviewerNotif').dom.style.display = 'none';
        $E('templateTable').dom.style.display = 'none';
    }
    if (value == "Content reviewing") {
        $E('steptitle').dom.style.display = '';
        $E('title').set('<%= _("content reviewing team")%>');
        $E('title').dom.style.display = '';
        $E('materialsTable').dom.style.display = 'none';
        $E('statusTable').dom.style.display = '';
        $E('reviewingQuestionsTable').dom.style.display = '';
        $E('editingCriteriaTable').dom.style.display = 'none';
        $E('defaultDueDatesTable').dom.style.display = '';
        $E('refereeDefaultDateRow').dom.style.display = '';
        $E('editorDefaultDateRow').dom.style.display = 'none';
        $E('reviewerDefaultDateRow').dom.style.display = '';
        $E('autoEmails').dom.style.display = ''
        $E('refereeNotif').dom.style.display = '';
        $E('editorNotif').dom.style.display = 'none';
        $E('reviewerNotif').dom.style.display = '';
        $E('refereeNotifForContribution').dom.style.display = '';
        $E('editorNotifForContribution').dom.style.display = 'none';
        $E('reviewerNotifForContribution').dom.style.display = '';
        $E('refereeJudgementNotif').dom.style.display = '';
        $E('editorJudgementNotif').dom.style.display = 'none';
        $E('reviewerJudgementNotif').dom.style.display = '';
        $E('authorSubmittedMatRefereeNotif').dom.style.display = '';
        $E('authorSubmittedMatEditorNotif').dom.style.display = 'none';
        $E('authorSubmittedMatReviewerNotif').dom.style.display = '';
        $E('templateTable').dom.style.display = '';
        
        //showReviewableMaterials();
        showReviewingStates();
        showReviewingQuestions();
        showDefaultReviewerDate();
        showDefaultRefereeDate();
        //showFormatChooser();
    }
    if (value == "Layout reviewing") {
        $E('steptitle').dom.style.display = '';
        $E('title').dom.style.display = '';
        $E('title').set('<%= _("layout reviewing team")%>');
        $E('materialsTable').dom.style.display = 'none';
        $E('statusTable').dom.style.display = 'none';
        $E('reviewingQuestionsTable').dom.style.display = 'none';
        $E('editingCriteriaTable').dom.style.display = '';
        $E('defaultDueDatesTable').dom.style.display = '';
        $E('refereeDefaultDateRow').dom.style.display = 'none';
        $E('editorDefaultDateRow').dom.style.display = '';
        $E('reviewerDefaultDateRow').dom.style.display = 'none';
        $E('autoEmails').dom.style.display = '';
        $E('refereeNotif').dom.style.display = 'none';
        $E('editorNotif').dom.style.display = '';
        $E('reviewerNotif').dom.style.display = 'none';
        $E('refereeNotifForContribution').dom.style.display = 'none';
        $E('editorNotifForContribution').dom.style.display = '';
        $E('reviewerNotifForContribution').dom.style.display = 'none';
        $E('refereeJudgementNotif').dom.style.display = 'none';
        $E('editorJudgementNotif').dom.style.display = '';
        $E('reviewerJudgementNotif').dom.style.display = 'none';
        $E('authorSubmittedMatRefereeNotif').dom.style.display = 'none';
        $E('authorSubmittedMatEditorNotif').dom.style.display = '';
        $E('authorSubmittedMatReviewerNotif').dom.style.display = 'none';
        $E('templateTable').dom.style.display = '';
        
        //showReviewableMaterials();
        showEditingCriteria();
        showDefaultEditorDate();
        //showFormatChooser();
    }
    if (value == "Content and layout reviewing") {
        $E('steptitle').dom.style.display = '';
        $E('title').set('<%= _("content and layout reviewing team")%>');
        $E('title').dom.style.display = '';
        $E('materialsTable').dom.style.display = 'none';
        $E('statusTable').dom.style.display = '';
        $E('reviewingQuestionsTable').dom.style.display = '';
        $E('editingCriteriaTable').dom.style.display = '';
        $E('defaultDueDatesTable').dom.style.display = '';
        $E('refereeDefaultDateRow').dom.style.display = '';
        $E('editorDefaultDateRow').dom.style.display = '';
        $E('reviewerDefaultDateRow').dom.style.display = '';
        $E('autoEmails').dom.style.display = '';
        $E('refereeNotif').dom.style.display = '';
        $E('editorNotif').dom.style.display = '';
        $E('reviewerNotif').dom.style.display = '';
        $E('refereeNotifForContribution').dom.style.display = '';
        $E('editorNotifForContribution').dom.style.display = '';
        $E('reviewerNotifForContribution').dom.style.display = '';
        $E('refereeJudgementNotif').dom.style.display = '';
        $E('editorJudgementNotif').dom.style.display = '';
        $E('reviewerJudgementNotif').dom.style.display = '';
        $E('authorSubmittedMatRefereeNotif').dom.style.display = '';
        $E('authorSubmittedMatEditorNotif').dom.style.display = '';
        $E('authorSubmittedMatReviewerNotif').dom.style.display = '';
        $E('templateTable').dom.style.display = '';
        
        //showReviewableMaterials();
        showReviewingStates();
        showReviewingQuestions();
        showDefaultReviewerDate();
        showDefaultRefereeDate();
        showEditingCriteria();
        showDefaultEditorDate();
        //showFormatChooser();
    }
}

new IndicoUI.Widgets.Generic.selectionField($E('inPlaceEditReviewingMode'),
                    'reviewing.conference.changeReviewingMode',
                    {conference: '<%= ConfReview.getConference().getId() %>'},
                    <%= ConferenceReview.reviewingModes[1:] %>,
                    "<%= ConfReview.getReviewingMode() %>",
                    observer);                    

/*var showReviewableMaterials = function() {
    new IndicoUI.Widgets.Generic.twoListField($E('inPlaceEditReviewableMaterials'),
                        10,"200px",<%=ConfReview.getNonReviewableMaterials()%>,<%=ConfReview.getReviewableMaterials()%>,
                        $T("Non reviewable materials"), $T("Reviewable materials"),
                        'reviewing.conference.changeReviewableMaterials',
                        {conference: '<%= ConfReview.getConference().getId() %>'},
                        '');
}*/

               
var showReviewingStates = function() {
    new IndicoUI.Widgets.Generic.keywordField(
        $E('inPlaceEditStates'),
        'multipleLinesListItem',
        'reviewing.conference.changeStates',
        {conference: '<%= ConfReview.getConference().getId() %>'},
        $T('Remove this status from the list')
    );
}

var showReviewingQuestions = function() {
    new IndicoUI.Widgets.Generic.keywordField(
        $E('inPlaceEditQuestions'),
        'multipleLinesListItem',
        'reviewing.conference.changeQuestions',
        {conference: '<%= ConfReview.getConference().getId() %>'},
        $T('Remove this question from the list')
    );
}

var showEditingCriteria = function() {
    new IndicoUI.Widgets.Generic.keywordField(
        $E('inPlaceEditCriteria'),
        'multipleLinesListItem',
        'reviewing.conference.changeCriteria',
        {conference: '<%= ConfReview.getConference().getId() %>'},
        $T('Remove this criteria from the list')
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

/*var deleteTemplate = function(tempId, tempName, rowId) {
                    var row = $E('TemplateRow_'+rowId);
                    var params = {conference: '<%= ConfReview.getConference().getId() %>',templateId: tempId} 
                    if (confirm("Are you sure you want to delete '"+ tempName+"'?")) {
                        var killProgress = IndicoUI.Dialogs.Util.progress($T('Removing...'));
                        jsonRpc(Indico.Urls.JsonRpcService,
                            'reviewing.conference.deleteTemplate',
                            params,
                            function(response,error) {
                                    if (exists(error)) {
                                        killProgress();
                                        IndicoUtil.errorReport(error);
                                    } else {
                                        $E('templateListTable').remove(row);
                                        killProgress();
                                    }
                                }
                    );
                    }
                };*/

var TemplateList = function(){
            <% keys = ConfReview.getTemplates().keys() %>
            <% for k in keys: %>
                <% t = ConfReview.getTemplates()[k] %>
                    var row = Html.tr({id:'TemplateRow_'+'<%=t.getId()%>'});
                var menu;
                    menu = Html.span(
                        {},
                        Widget.link(command( function(){
                            var params = {conference: <%= ConfReview.getConference().getId() %>,templateId: '<%=t.getId()%>'}
		                    if (confirm("Are you sure you want to delete '"+ '<%=t.getName()%>'+"'?")) {
		                        var killProgress = IndicoUI.Dialogs.Util.progress($T('Removing...'));
		                        jsonRpc(Indico.Urls.JsonRpcService,
		                            'reviewing.conference.deleteTemplate',
		                            params,
		                            function(response,error) {
		                                    if (exists(error)) {
		                                        killProgress();
		                                        IndicoUtil.errorReport(error);
		                                    } else {
		                                        killProgress();
		                                        $E('templateListTable').remove($E('TemplateRow_'+'<%=t.getId()%>'));
		                                        tablerows = document.getElementById('templateListTable').rows.length;
				                                if(tablerows == '1'){
				                                    $E('NoTemplateTable').dom.style.display = '';
				                                    $E('templateListTableAll').dom.style.display = 'none';}
		                                    }
		                                }
		                    );}
                           },
                            IndicoUI.Buttons.removeButton()
                        )));
                    var linkName = Html.a({href: "<%= urlHandlers.UHDownloadContributionTemplate.getURL() %>" + "?reviewingTemplateId=" + '<%= t.getId()%>' + "&confId=<%= ConfReview.getConference().getId()%>", style:{color:'#5FA5D4'}}, '<%= t.getName()%>');
                    var cellName = Html.td({id:'TemplateName_'+'<%= t.getId()%>', style:{borderRight: '5px solid #FFFFFF', borderLeft:'5px solid #FFFFFF'}}, linkName);
                    cellName.append(linkName);
                    <% if CanDelete: %>
                        cellName.append(menu);
                    <% end %>
                    var cellFormat = Html.td({id:'TemplateName_'+'<%= t.getId()%>', style:{borderRight: '5px solid #FFFFFF', borderLeft:'5px solid #FFFFFF'}}, '<%= t.getFormat()%>');
                    var cellDescription = Html.td({id:'TemplateName_'+'<%= t.getId()%>', style:{borderRight: '5px solid #FFFFFF', borderLeft:'5px solid #FFFFFF'}}, '<%= t.getDescription()%>');
                    row.append(cellName);
                    row.append(cellFormat);
                    row.append(cellDescription);        
                    $E('templateListTable').append(row); 
             <% end %>
            
          }  
  

$E('refereeNotifButton').set(IndicoUI.Widgets.Generic.switchOptionButton('reviewing.conference.RefereeEmailNotif', 
                                            {conference: '<%= ConfReview.getConference().getId() %>',
                                            AutoEmailsToChange: 'Referee'}, 
                                            'When a Referee is added or removed from the team',
                                            true
)); 
$E('reviewerNotifButton').set(IndicoUI.Widgets.Generic.switchOptionButton('reviewing.conference.ReviewerEmailNotif', 
                                            {conference: '<%= ConfReview.getConference().getId() %>',
                                            AutoEmailsToChange: 'Reviewer'}, 
                                            'When a Content Reviewer is added or removed from the team',
                                            true
));
$E('editorNotifButton').set(IndicoUI.Widgets.Generic.switchOptionButton('reviewing.conference.EditorEmailNotif', 
                                            {conference: '<%= ConfReview.getConference().getId() %>',
                                            AutoEmailsToChange: 'Editor'}, 
                                            'When a Layout Reviewer is added or removed from the team',
                                            true
));
$E('refereeNotifForContributionButton').set(IndicoUI.Widgets.Generic.switchOptionButton('reviewing.conference.RefereeEmailNotifForContribution', 
                                            {conference: '<%= ConfReview.getConference().getId() %>',
                                            AutoEmailsToChange: 'Referee'}, 
                                            'When a contribution is assigned or unassigned to a Referee',
                                            true
));
$E('reviewerNotifForContributionButton').set(IndicoUI.Widgets.Generic.switchOptionButton('reviewing.conference.ReviewerEmailNotifForContribution', 
                                            {conference: '<%= ConfReview.getConference().getId() %>',
                                            AutoEmailsToChange: 'Reviewer'}, 
                                            'When a contribution is assigned or unassigned to a Content Reviewer',
                                            true
));
$E('editorNotifForContributionButton').set(IndicoUI.Widgets.Generic.switchOptionButton('reviewing.conference.EditorEmailNotifForContribution', 
                                            {conference: '<%= ConfReview.getConference().getId() %>',
                                            AutoEmailsToChange: 'Editor'}, 
                                            'When a contribution is assigned or unassigned to a Layout Reviewer',
                                            true
));
$E('refereeJudgementNotifButton').set(IndicoUI.Widgets.Generic.switchOptionButton('reviewing.conference.RefereeEmailJudgementNotif', 
                                            {conference: '<%= ConfReview.getConference().getId() %>',
                                            AutoEmailsToChange: 'Referee'}, 
                                            'To the author when the Referee submits judgement',
                                            true
));
$E('reviewerJudgementNotifButton').set(IndicoUI.Widgets.Generic.switchOptionButton('reviewing.conference.ReviewerEmailJudgementNotif', 
                                            {conference: '<%= ConfReview.getConference().getId() %>',
                                            AutoEmailsToChange: 'Reviewer'}, 
                                            'To the author when a Content Reviewer submits judgement',
                                            true
));
$E('editorJudgementNotifButton').set(IndicoUI.Widgets.Generic.switchOptionButton('reviewing.conference.EditorEmailJudgementNotif', 
                                            {conference: '<%= ConfReview.getConference().getId() %>',
                                            AutoEmailsToChange: 'Editor'}, 
                                            'To the author when the Layout Reviewer submits judgement',
                                            true
));
$E('authorSubmittedMatRefereeNotif').set(IndicoUI.Widgets.Generic.switchOptionButton('reviewing.conference.AuthorSubmittedMatRefereeNotif', 
                                            {conference: '<%= ConfReview.getConference().getId() %>',
                                            AutoEmailsToChange: 'Referee'}, 
                                            'To the Referee when an author submits paper',
                                            true
));
$E('authorSubmittedMatReviewerNotif').set(IndicoUI.Widgets.Generic.switchOptionButton('reviewing.conference.AuthorSubmittedMatEditorNotif', 
                                            {conference: '<%= ConfReview.getConference().getId() %>',
                                            AutoEmailsToChange: 'Reviewer'}, 
                                            'To the Content Reviewer when an author submits paper',
                                            true
));
$E('authorSubmittedMatEditorNotif').set(IndicoUI.Widgets.Generic.switchOptionButton('reviewing.conference.AuthorSubmittedMatReviewerNotif', 
                                            {conference: '<%= ConfReview.getConference().getId() %>',
                                            AutoEmailsToChange: 'Editor'}, 
                                            'To the Layout Reviewer when an author submits paper',
                                            true
));


/* IndicoUI.executeOnLoad(function(){
    var pm = new IndicoUtil.parameterManager(); 
    return $E('formatchooser').set(showFormatChooser(pm));
});


function showFormatChooser(pm){
    var select = Html.select({name: 'format'}, Html.option({value: "Unknown"}, "--Select a format--")<% for f in Template.formats: %>,Html.option({value: "<%= f %>"}, "<%= f %>")<%end%>);
    var text = Html.edit({name: 'formatOther'});
    var chooser = new Chooser(new Lookup({
            select: function() {
                pm.remove(text);
                pm.add(select);
               var sel = '<select name="format" id="defaultformat">'+
                         '<option value="Unknown"><%= _("--Select a format--")%></option>'+  
<% for f in Template.formats: %> 
                         '<option value="<%= f %>"><%= f %></option>'+
<% end %>
                         '</select>';
                return Html.div({},select,
                         " ",
                         $T("or"),
                         " ",
                         Widget.link(command(function() {
                             chooser.set('write');
                         }, $T("other"))));
            },

            write: function() {
                bind.detach(select);
                pm.remove(select);
                pm.add(text);
                return Html.div({}, text,
                                " ",
                               $T("or"),
                               " ",
                                Widget.link(command(function() {
                                    chooser.set('select');
                                }, $T("select from list"))));
            }
        }));
        chooser.set('select');

        return Widget.block(chooser);
}
 */
                 
<% if ConfReview.hasReviewing(): %>
    //showReviewableMaterials();
    TemplateList();
    
    $E('uploadTpl').observeClick(function(){ var popup = new UploadTemplateDialog( 'Upload Template',
        {conference: '<%= ConfReview.getConference().getId() %>'}, '350px', '30px',
        <%= jsonEncode(Template.formats.keys()) %>, '<%= urlHandlers.UHSetTemplate.getURL() %>',
        function(value) {
            $E('NoTemplateTable').dom.style.display = 'none';
            $E('templateListTableAll').dom.style.display = '';
            
	        /* this is a little hack who is needed to get the URL of the new uploaded template*/
	        //linkDelete = "<%= urlHandlers.UHDeleteContributionTemplate.getURL() %>" + "?reviewingTemplateId=" + value.id + "&confId=<%= ConfReview.getConference().getId()%>";
            //var deleteIcon = Html.img({className: 'imglink',style:{paddingLeft: '20px', verticalAlign: 'bottom', width: '15px', height: '15px'}, alt: 'delete template', src: imageSrc("remove")});
            //var deleteLink = Html.a({href: linkDelete},deleteIcon);
            
            var row = Html.tr();
            var params = {conference: '<%= ConfReview.getConference().getId() %>',templateId: value.id}
            var deleteTemplate = function() {
            if (confirm("Are you sure you want to delete '"+ value.name+"'?")) {
                var killProgress = IndicoUI.Dialogs.Util.progress($T('Removing...'));
	            jsonRpc(Indico.Urls.JsonRpcService,
		            'reviewing.conference.deleteTemplate',
		            params,
		            function(response,error) {
                            if (exists(error)) {
                                killProgress();
                                IndicoUtil.errorReport(error);
                            } else {
                                killProgress();
                                $E('templateListTable').remove(row);
                                tablerows = document.getElementById('templateListTableAll').rows.length;
                                if(tablerows == '1'){
                                    $E('NoTemplateTable').dom.style.display = '';
                                    $E('templateListTableAll').dom.style.display = 'none';}
                            }
                        });}};
        var menu;
            menu = Html.span(
                {},
                Widget.link(command(
                    deleteTemplate,
                    IndicoUI.Buttons.removeButton()
                )));
            var linkName = Html.a({href: "<%= urlHandlers.UHDownloadContributionTemplate.getURL() %>" + "?reviewingTemplateId=" + value.id + "&confId=<%= ConfReview.getConference().getId()%>", style:{color:'#5FA5D4'}}, value.name);
            var cellName = Html.td({id:'TemplateName_'+value.id, style:{borderRight: '5px solid #FFFFFF', borderLeft:'5px solid #FFFFFF'}}, linkName);
            cellName.append(linkName);
            <% if CanDelete: %>
                cellName.append(menu);
            <% end %>
            var cellFormat = Html.td({id:'TemplateName_'+value.id, style:{borderRight: '5px solid #FFFFFF', borderLeft:'5px solid #FFFFFF'}}, value.format);
            var cellDescription = Html.td({id:'TemplateName_'+value.id, style:{borderRight: '5px solid #FFFFFF', borderLeft:'5px solid #FFFFFF'}}, value.description);
            row.append(cellName);
            row.append(cellFormat);
            row.append(cellDescription);
            
            return $E('templateListTable').append(row);      
        
            }); popup.open();
            }
            ); 
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