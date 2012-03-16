<table width="100%">
<%include file="ConfContributionListFilters.tpl"/>

    <tr>
        <td>
            <a name="contributions"></a>
            <table align="center" width="100%" border="0" cellpadding="0" cellspacing="0">
                <tr>
                    <td colspan="9">
                        <a name="contribs"></a>
                        <table cellpadding="0" cellspacing="0">
                            <tr>
                                <td class="groupTitle" width="100%" style="margin-bottom: 20px;">${ _("Contribution List")} (${ numContribs })</td>
                                <td nowrap align="right" style="border-bottom: 1px solid #777777;">
                                % if startContrib != 1:
                                    <a href="${previousContribsURL}">
                                        <img src="${Config.getInstance().getSystemIconURL('arrow_previous')}" border="0" style="vertical-align:middle" alt="">
                                    </a>
                                % endif
                                ${_(" showing ") + str(startContrib) + "-" + str(endContrib)}
                                % if endContrib < numContribs:
                                    <a href="${nextContribsURL}">
                                        <img src="${Config.getInstance().getSystemIconURL('arrow_next')}" border="0" style="vertical-align:middle" alt="">
                                    </a>
                                % endif
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <tr>
                    <td colspan="9"><br /><br /></td>
                </tr>
                <tr>
                    <td></td>
                    <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
                        % if currentSorting == "number":
                            <img src='${Config.getInstance().getSystemIconURL(sortingOrder + "Arrow")}' alt="${sortingOrder}">
                        % endif
                        <a href=${ getOrderURL("number") }> ${ _("Id")}</a>
                    </td>
                    <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
                       % if currentSorting == "date":
                            <img src='${Config.getInstance().getSystemIconURL(sortingOrder + "Arrow")}' alt="${sortingOrder}">
                        % endif
                        <a href=${ getOrderURL("date") }> ${ _("Date")}</a>
                    </td>
                    % if len(conf.getContribTypeList()) > 0:
                        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
                        % if currentSorting == "type":
                            <img src='${Config.getInstance().getSystemIconURL(sortingOrder + "Arrow")}' alt="${sortingOrder}">
                        % endif
                            <a href=${ getOrderURL("type") }> ${_("Type")}</a>
                        </td>
                    % endif
                    <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
                        % if currentSorting == "title":
                            <img src='${Config.getInstance().getSystemIconURL(sortingOrder + "Arrow")}' alt="${sortingOrder}">
                        % endif
                        <a href=${ getOrderURL("title") }> ${ _("Title")}</a>
                    </td>
                    <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
                        % if currentSorting == "speaker":
                            <img src='${Config.getInstance().getSystemIconURL(sortingOrder + "Arrow")}' alt="${sortingOrder}">
                        % endif
                        <a href=${ getOrderURL("speaker") }> ${ _("Presenter")}</a>
                    </td>
                    <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
                        % if currentSorting == "session":
                            <img src='${Config.getInstance().getSystemIconURL(sortingOrder + "Arrow")}' alt="${sortingOrder}">
                        % endif
                        <a href=${ getOrderURL("session") }> ${ _("Session")}</a>
                    </td>
                    % if len(conf.getTrackList()) > 0:
                        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
                        % if currentSorting == "track":
                            <img src='${Config.getInstance().getSystemIconURL(sortingOrder + "Arrow")}' alt="${sortingOrder}">
                        % endif
                            <a href=${ getOrderURL("track") }> ${_("Track")}</a>
                        </td>
                    % endif
                    <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> ${ _("Files")}</td>
                    % if showAttachedFiles:
                        <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;"> ${ _("Abstracts")}</td>
                    % endif

                </tr>
                <form action=${ contribSelectionAction } method="post" target="_blank">
                    % for contrib in contributions:
                        % if contrib.canAccess(accessWrapper):
                            <%include file="ConfContributionListContribFull.tpl" args="contrib=contrib"/>
                        % else:
                            <%include file="ConfContributionListContribMin.tpl" args="contrib=contrib"/>
                        % endif
                    % endfor
                <tr>
                    <td colspan="9" align="right">
                        % if startContrib != 1:
                            <a href="${previousContribsURL}">
                                <img src="${Config.getInstance().getSystemIconURL('arrow_previous')}" border="0" style="vertical-align:middle" alt="">
                            </a>
                        % endif
                        ${_("showing")+ str(startContrib) + "-" + str(endContrib)} "
                        % if sendContrib < numContribs:
                            <a href="${nextContribsURL}">
                                <img src="${Config.getInstance().getSystemIconURL('arrow_next')}" border="0" style="vertical-align:middle" alt="">
                            </a>
                        % endif
                    </td>
                </tr>
                <tr>
                    <td colspan="9" valign="bottom" align="left">
                        <input type="submit" class="btn" name="PDF" value="${ _("booklet of selected contributions")}" style="width:264px">
                    </td>
                </tr>
                </form>
                <tr>
                    <form action=${ contributionsPDFURL } method="post" target="_blank">
                    <td colspan="9" valign="bottom" align="left">
                        % for contribId in contribsToPrint:
                            <input type="hidden" name="contributions" value="${contribId}">
                        % endfor
                        <input type="submit" class="btn" value="${ _("booklet of all contributions")}" style="width:264px">
                    </td>
                    </form>
                </tr>
                <tr><td colspan="9">&nbsp;</td></tr>
            </table>
        </td>
    </tr>
</table>
