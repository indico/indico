<% import MaKaC.webinterface.urlHandlers as urlHandlers %>

% for review in Versioning:
    % if review.materials and (( (ConferenceChoice == 2 or ConferenceChoice == 4) and review.getRefereeJudgement().isSubmitted() ) or ( ConferenceChoice == 3 and review.getEditorJudgement().isSubmitted())):
    <div class="historyReview">
        <h1 class="historyReviewHeader">${ _("Review") } ${ review.getVersion() }</h1>
        <h2>${_("Files")}</h2>
        <ul style="list-style: none outside none; padding: 0 0 0 20px">
            % for paper_file in review.materials:
                <li><span style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                    <a href="${ url_for('paper_reviewing.download_paper_file', paper_file) }" target="_blank">
                        ${ paper_file.filename }
                    </a>
                    (<span style="font-style:italic;">
                        ${_("Uploaded on")} ${ paper_file.created_dt.strftime("%d %b %Y %H:%M")}
                    </span>)
                </li>
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
