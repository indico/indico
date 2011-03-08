<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.conference import LocalFile %>
<% from MaKaC.conference import Link %>

% for review in Versioning:
        % for m in review.getMaterials():
           % for res in m.getResourceList():
            <table width="90%" align="center" border="0" style="padding-bottom: 10px;">
                <tr>
                    <td colspan="1" class="dataCaptionTD" style="width: 25%;padding-right: 1px">
                     <em>${ _("Review") } ${ review.getVersion() }<span class="titleCellFormat" style="font-size: 12px;">${ _(":")}</span></em>
                    </td>
                    <td>
                            <span style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                            % if isinstance(res, LocalFile):
                                <a href="${ urlHandlers.UHFileAccess.getURL(res) }">
                            % elif isinstance(res, Link) :
                                <a href="${ res.getURL() }">
                            % endif
                                ${ res.getName() }
                            </a>
                            </span>
                        <br/>
                    </td>
                </tr>
            </table>
           % endfor
         % endfor

        <%include file="ContributionReviewingDisplay.tpl" args="Editing = review.getEditorJudgement(), AdviceList = review.getReviewerJudgements(), Review = review,
                        ConferenceChoice = ConferenceChoice"/>
% endfor