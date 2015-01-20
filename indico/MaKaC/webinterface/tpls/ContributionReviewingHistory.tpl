<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.conference import LocalFile %>
<% from MaKaC.conference import Link %>

% for review in Versioning:
    % if review.getMaterials() and (( (ConferenceChoice == 2 or ConferenceChoice == 4) and review.getRefereeJudgement().isSubmitted() ) or ( ConferenceChoice == 3 and review.getEditorJudgement().isSubmitted())):
    <div class="historyReview">
        <h1 class="historyReviewHeader">${ _("Review") } ${ review.getVersion() }</h1>
        <h2>${_("Files")}</h2>
        <ul style="list-style: none outside none; padding: 0 0 0 20px">
            % for m in review.getMaterials():
               % for res in m.getResourceList():
                    <li><span style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                        <a href="${ urlHandlers.UHFileAccess.getURL(res) if isinstance(res, LocalFile) else res.getURL()}" target="_blank">
                            ${ res.getName() }
                        </a>
                        (<span style="font-style:italic;">${_("Uploaded on")} ${res.getCreationDate().strftime("%d %b %Y %H:%M")}</span>)
                    </li>
               % endfor
             % endfor
        </ul>
        <div>
        <h2>${_("Assessments")}</h2>
            <%include file="ContributionReviewingDisplay.tpl" args="Editing = review.getEditorJudgement(), AdviceList = review.getReviewerJudgements(), Review = review,
                            ConferenceChoice = ConferenceChoice"/>
        </div>
     </div>
    % endif
% endfor
