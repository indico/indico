<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.webinterface.rh.conferenceBase import RHSubmitMaterialBase %>
<%= existingMaterialsTitle %>
<div id="reviewingMaterialListPlace"><!-- DOM-filled materials list --></div>
<span id="container"></span>
<% if self._target.getReviewManager().getLastReview().isAuthorSubmitted(): %>
    <% display = 'none' %>
<% end %>
<% else: %>
    <% display = 'form' %>
<% end %>
<form id="SendBtnForm" action="<%=urlHandlers.UHContributionSubmitForRewiewing.getURL(self._target)%>" method="POST" style="disabled:true; display:<%=display%>">
    <input id="SendBtn" type="submit" class="btn" value="Send" disabled="disabled" style="display:<%=display%>">
    <span id="SendHelp" style="display:<%=display%>">
        <% inlineContextHelp(_('First you should add the materials and then by clicking on this button you will send them for reviewing. They will be locked until the end of the process')) %>
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
     <% if  self._target.getConference().getConfReview().getChoice() == 3: %>
        <% if not self._target.getReviewManager().getLastReview().isAuthorSubmitted() and not self._target.getReviewManager().getLastReview().getEditorJudgement().isSubmitted():%>
            visibility = 'visible';
        <% end %>
        <% else: %>
            visibility = 'hidden';
        <% end %>
    <% end %>
    <% if self._target.getConference().getConfReview().getChoice() == 2: %>
        <% if not self._target.getReviewManager().getLastReview().isAuthorSubmitted() and not (self._target.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted() or self._target.getReviewManager().getLastReview().anyReviewerHasGivenAdvice()): %>
            visibility = 'visible';
        <% end %>
        <% else: %>
            visibility = 'hidden';
        <% end %>
    <% end %>
    <% if  self._target.getConference().getConfReview().getChoice() == 4: %>
        <% if not self._target.getReviewManager().getLastReview().isAuthorSubmitted() and not (self._target.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted() or self._target.getReviewManager().getLastReview().anyReviewerHasGivenAdvice() or self._target.getReviewManager().getLastReview().getEditorJudgement().isSubmitted()): %>
            visibility = 'visible';
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
</script>
