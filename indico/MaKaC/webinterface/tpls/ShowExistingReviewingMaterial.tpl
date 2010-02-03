<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.webinterface.rh.conferenceBase import RHSubmitMaterialBase %>
%(existingMaterialsTitle)s
<div id="reviewingMaterialListPlace"><!-- DOM-filled materials list --></div>
<span id="container"></span>
                                   
<script type="text/javascript">

<% import MaKaC.conference as conference %>

var args = {
        conference: '<%= self._target.getConference().getId() %>',
        confId: '<%= self._target.getConference().getId() %>',
        contribution: '<%= self._target.getId() %>',
        contribId: '<%= self._target.getId() %>'
    };
    var uploadAction = Indico.Urls.UploadAction.contribution;
    var visibility = '';
                                 <% if  self._target.getConference().getConfReview().getChoice() == 3: %> 
                                    <% if not self._target.getReviewManager().getLastReview().getEditorJudgement().isSubmitted():%>
                                        visibility = 'visible';
                                    <% end %>
                                    <% else: %>
                                        visibility = 'hidden';
                                    <% end %>
                                <% end %>
                                <% if self._target.getConference().getConfReview().getChoice() == 2: %>
                                    <% if not (self._target.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted() or self._target.getReviewManager().getLastReview().anyReviewerHasGivenAdvice()): %>
                                        visibility = 'visible';
                                    <% end %>
                                    <% else: %>
                                        visibility = 'hidden';
                                    <% end %>
                                <% end %>
                                <% if  self._target.getConference().getConfReview().getChoice() == 4: %>
                                    <% if not (self._target.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted() or self._target.getReviewManager().getLastReview().anyReviewerHasGivenAdvice() or self._target.getReviewManager().getLastReview().getEditorJudgement().isSubmitted()): %>                              
                                        visibility = 'visible';
                                    <% end %>
                                    <% else: %>
                                        visibility = 'hidden';
                                    <% end %>
                                <% end %>
    
    
var mlist = new ReviewingMaterialListWidget(args, <%= RHSubmitMaterialBase._allowedMatsforReviewing %>, uploadAction);

$E('reviewingMaterialListPlace').set(mlist.draw());

</script>

