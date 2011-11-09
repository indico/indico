<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.paperReviewing import ConferencePaperReview as CPR %>

<table width="100%" align="center">
  <tr>
    <td>
      <table align="center" width="95%" border="0" style="border: 1px solid #777777;">
        <tr>
          <td>&nbsp;</td>
        </tr>
        <tr>
          <td>
            <table align="center" width="95%" border="0">
              ${ withdrawnNotice }
              <tr>
                <td align="center">${ modifIcon }<font size="+1" color="black"><b>${ title }</b></font></td>
              </tr>
              <tr>
                <td width="100%">&nbsp;</td>
              </tr>
              % if not self_._rh._target.getConference().getAbstractMgr().isActive() or not self_._rh._target.getConference().hasEnabledSection("cfa") or not self_._rh._target.getConference().getAbstractMgr().hasAnyEnabledAbstractField():
              <tr>
                 <td>
                  <table align="center">
                    <tr>
                      <td>${ description }</td>
                    </tr>
                  </table>
                </td>
              </tr>
              <tr>
                <td width="100%">&nbsp;<td>
              </tr>
              % endif
    <tr>
      <td>
            <table align="center" width="95%">
                <tr>
                <td colspan="2">
                % if hideInfo:
                    <% display = '' %>
                % else:
                    <% display = 'none' %>
                % endif
                <div align="center" style="display:${display}">
                    <span id="hideContributionFull" class="collaborationDisplayMoreInfo" onclick="showGeneralInfo();">${ _("Show general info")}</span>
                </div>
                % if hideInfo:
                    <% display = 'none' %>
                % else:
                    <% display = '' %>
                % endif
                <div id="showContributionFull" style="display:${display}">
                <table align="center" width="95%">
                % if self_._rh._target.getConference().getAbstractMgr().isActive() and self_._rh._target.getConference().hasEnabledSection("cfa") and self_._rh._target.getConference().getAbstractMgr().hasAnyEnabledAbstractField():
            ${ additionalFields }
                % endif
        <tr>
          <td align="right" valign="top" class="displayField"><b>${ _("Id")}:</b></td>
              <td>${ id }</td>
            </tr>
        ${ location }
            <tr>
                <td align="right" valign="top" class="displayField"><b>${ _("Starting date")}:</b></td>
            <td width="100%">
                <table cellspacing="0" cellpadding="0" align="left">
                <tr>
                    <td align="right">${ startDate }</td>
                <td>&nbsp;&nbsp;${ startTime }</td>
                </tr>
                </table>
            </td>
            </tr>
            <tr>
                <td align="right" valign="top" class="displayField"><b>${ _("Duration")}:</b></td>
                <td width="100%">${ duration }</td>
            </tr>
                    ${ contribType }
                    ${ primaryAuthors }
                    ${ coAuthors }
                    ${ speakers }
                    % if (Contribution.canUserSubmit(self_._aw.getUser()) or Contribution.canModify(self_._aw)) and not isWithdrawn:
                        <td class="displayField" nowrap="" align="right" valign="top">
                            <b>${_("Material")}:</b>
                            % if Contribution.getConference() and Contribution.getConference().hasEnabledSection('paperReviewing') and Contribution.getConference().getConfPaperReview().hasReviewing() :
                                ${inlineContextHelp(_('Here you should add the general materials for your contribution. They will not be subject of reviewing.'))}
                            % endif
                        </td>
                        <td width="100%" valign="top" style="padding-top:5px;">
                            ${MaterialList}
                        </td>
                    % else:
                        ${ material }
                    % endif
                    ${ inSession }
                    ${ inTrack }
                    ${ subConts }
                </table>
                </div>
                </td>
                </tr>

                    % if Contribution.getConference() and Contribution.getConference().hasEnabledSection('paperReviewing') and Contribution.getConference().getConfPaperReview().hasReviewing() and not isWithdrawn:
                        % if Contribution.canUserSubmit(self_._aw.getUser()) or Contribution.canModify(self_._aw):
                        <tr><td align="right" valign="top" class="displayField" nowrap>
                                <b>${_("Reviewing material")}:</b>
                                ${inlineContextHelp(_('Here you should add the materials for reviewing. They will be judged by the reviewing team.'))}
                            </td>
                            <td>
                                ${ReviewingMatList}
                            </td>
                        </tr>
                            % if Contribution.getReviewManager().getLastReview().isAuthorSubmitted():
                                    <tr>
                                    <td align="right" valign="top" class="displayField" nowrap>
                                        <b>${_("Reviewing status")}:</b>
                                    </td>
                                    <td style="border-left:5px solid #FFFFFF;">
                                        ${ "<br>".join(Contribution.getReviewManager().getLastReview().getReviewingStatus(forAuthor = True)) }
                                    </td>
                                </tr>
                                % if  Contribution.getConference().getConfPaperReview().getChoice() == CPR.LAYOUT_REVIEWING:
                                    % if not Contribution.getReviewManager().getLastReview().getEditorJudgement().isSubmitted():
                                        <% display = 'table' %>
                                    % else:
                                        <% display = 'none' %>
                                    % endif
                                % endif
                                % if Contribution.getConference().getConfPaperReview().getChoice() == CPR.CONTENT_REVIEWING:
                                    % if not (Contribution.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted() or Contribution.getReviewManager().getLastReview().anyReviewerHasGivenAdvice()):
                                        <% display = 'table' %>
                                    % else:
                                        <% display = 'none' %>
                                    % endif
                                % endif
                                % if  Contribution.getConference().getConfPaperReview().getChoice() == CPR.CONTENT_AND_LAYOUT_REVIEWING:
                                    % if Contribution.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted() or Contribution.getReviewManager().getLastReview().anyReviewerHasGivenAdvice() or Contribution.getReviewManager().getLastReview().getEditorJudgement().isSubmitted():
                                        <% display = 'none' %>
                                    % else:
                                        <% display = 'table' %>
                                    % endif
                                % endif
                          % else:
                            <tr>
                                <td></td>
                                <td></td>
                            </tr>
                          % endif
                      % if len(Contribution.getReviewManager().getVersioning()) > 1:
                      <tr>
                              <td align="right" valign="top" class="displayField" nowrap>
                                    <b>${_("Reviewing history")}:</b>
                              </td>
                              <td width="100%" valing="top"><div id="showHideHistory" style="display:inline"></div></td>
                   </tr>
                   <tr>
                       <td id="HistoryTable" align="center" width="100%" colspan="2">
                           ${ reviewingHistoryStuffDisplay }
                       </td>
               </tr>

              % endif
              % endif
              % endif
              </table>
                 </td>
              </tr>
              </table>
           </td>
        </tr>
        </table>
    </td>
</tr>
</table>

<script type="text/javascript">
/**
 * Builds the 'link' to show and hide the reviewing history.
 */
var buildShowHideHistory = function() {
    var option = new Chooser({
        showHistory: command(function(){
            $E('HistoryTable').dom.style.display = '';
            option.set('hideHistory');
        }, $T('Show History')),
        hideHistory: command(function(){
            $E('HistoryTable').dom.style.display = 'none';
            option.set('showHistory');
        }, $T('Hide History'))
    });
    option.set('showHistory');

    $E('showHideHistory').set(Widget.link(option));
}

% if len(Contribution.getReviewManager().getVersioning()) > 1:
buildShowHideHistory();
$E('HistoryTable').dom.style.display = 'none';
% endif

function showGeneralInfo() {
    if ($E('hideContributionFull').dom.innerHTML == 'Hide general info') {
        $E('showContributionFull').dom.style.display = 'none';
        $E('hideContributionFull').dom.innerHTML = 'Show general info';
    } else {
        if ($E('hideContributionFull').dom.innerHTML == 'Show general info') {
            $E('showContributionFull').dom.style.display = '';
            $E('hideContributionFull').dom.innerHTML = $T('Hide general info');
        }
    }
}

</script>
