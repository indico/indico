<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.webinterface.rh.conferenceBase import RHSubmitMaterialBase %>
<% from MaKaC.paperReviewing import ConferencePaperReview as CPR %>

<div id="showStep1" class="groupTitleSmallPaper"><span><%= _("Step 1 - Upload paper") %></span></div>
<%= existingMaterialsTitle %>
<div id="reviewingMaterialListPlace"><!-- DOM-filled materials list --></div>
<span id="container"></span>
<% if self._target.getReviewManager().getLastReview().isAuthorSubmitted(): %>
    <% display = 'none' %>
<% end %>
<% else: %>
    <% display = 'form' %>
<% end %>
<div id="showStep2" class="groupTitleSmallPaper"><span><%= _("Step 2 - Submit the paper") %></span></div>
<form id="SendBtnForm" action="<%=urlHandlers.UHContributionSubmitForRewiewing.getURL(self._target)%>" method="POST" style="disabled:true; display:<%=display%>">
    <div id="reviewingWarning" style="padding-bottom:3px; padding-left:3px;">
        <span class="collaborationWarning">Note that you cannot modify the reviewing materials after submitting them.</span>
    </div>
    <input id="SendBtn" type="submit" onclick="javascript:return confirm($T('Do you want to send the paper for reviewing? After sending it, you will not be able to submit another file until it is reviewed.'));" class="btn" value="Submit" disabled="disabled" style="display:<%=display%>">
    <span id="SendHelp" style="display:<%=display%>">
        <% inlineContextHelp(_('First you should add the materials and then by clicking on this button you will submit them for reviewing. They will be locked until the end of the process')) %>
    </span>
</form>
<script type="text/javascript">

<% import MaKaC.conference as conference %>
<% from MaKaC.webinterface.materialFactories import MaterialFactoryRegistry %>

var args = {
        conference: '<%= self._target.getConference().getId() %>',
        confId: '<%= self._target.getConference().getId() %>',
        contribution: '<%= self._target.getId() %>',
        contribId: '<%= self._target.getId() %>',
        parentProtected: <%= jsBoolean(self._target.getAccessController().isProtected()) %>
    };

    var uploadAction = Indico.Urls.UploadAction.contribution;
    var visibility = '';
     <% if  self._target.getConference().getConfPaperReview().getChoice() == CPR.LAYOUT_REVIEWING: %>
        <% if not self._target.getReviewManager().getLastReview().isAuthorSubmitted() and not self._target.getReviewManager().getLastReview().getEditorJudgement().isSubmitted():%>
            <% if showSendButton: %>
                visibility = 'visible';
            <% end %>
            <% else: %>
                visibility = 'hidden';
            <% end %>
        <% end %>
        <% else: %>
            visibility = 'hidden';
        <% end %>
    <% end %>
    <% if self._target.getConference().getConfPaperReview().getChoice() == CPR.CONTENT_REVIEWING: %>
        <% if not self._target.getReviewManager().getLastReview().isAuthorSubmitted() and not (self._target.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted() or self._target.getReviewManager().getLastReview().anyReviewerHasGivenAdvice()): %>
            <% if showSendButton: %>
                visibility = 'visible';
            <% end %>
            <% else: %>
                visibility = 'hidden';
            <% end %>
        <% end %>
        <% else: %>
            visibility = 'hidden';
        <% end %>
    <% end %>
    <% if  self._target.getConference().getConfPaperReview().getChoice() == CPR.CONTENT_AND_LAYOUT_REVIEWING: %>
        <% if not self._target.getReviewManager().getLastReview().isAuthorSubmitted() and not (self._target.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted() or self._target.getReviewManager().getLastReview().anyReviewerHasGivenAdvice() or self._target.getReviewManager().getLastReview().getEditorJudgement().isSubmitted()): %>
            <% if showSendButton: %>
                visibility = 'visible';
            <% end %>
            <% else: %>
                visibility = 'hidden';
            <% end %>
        <% end %>
        <% else: %>
            visibility = 'hidden';
        <% end %>
    <% end %>

var mlist = new ReviewingMaterialListWidget(args, [["reviewing", "Reviewing"]], uploadAction,null, null, visibility, $E("SendBtn"));

$E('reviewingMaterialListPlace').set(mlist.draw());

<% if self._target.getReviewManager().getLastReview().isAuthorSubmitted(): %>
   $E('SendBtnForm').dom.style.display = 'none';
<% end %>

<% if showSendButton: %>
    $E('SendBtnForm').dom.style.display = '';
<% end %>
<% else: %>
    $E('SendBtnForm').dom.style.display = 'none';
<% end %>

if (visibility == 'visible') {
    $E('showStep1').dom.style.display = '';
    $E('showStep2').dom.style.display = '';
} else {
    $E('showStep1').dom.style.display = 'none';
    $E('showStep2').dom.style.display = 'none';
}

</script>
