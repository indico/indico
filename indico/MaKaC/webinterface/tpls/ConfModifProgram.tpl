<div class="groupTitle">
    ${ _("Programme Description")}
</div>
<table width="90%" align="center" border="0">
    <tr>
        <td class="dataCaptionTD">
            <span class="dataCaptionFormat">${ _("Description")}</span>
        </td>
        <td>
            <div class="blacktext" id="inPlaceEditDescription">${conf.getDescription()}</div>
        </td>
    </tr>
</table>
<div class="groupTitle">
    ${ _("Tracks")}
</div>
<table width="90%" align="center" border="0">
    <tr>
        <td bgcolor="white" width="100%" colspan="4" align="center">
            <form action="${ deleteItemsURL }" method="POST">
            % if len(conf.getTrackList()) == 0:
                ${_("No track defined")}
            % else:
            <table cellspacing="0" cellpadding="5" width="100%%">
            % for track in conf.getTrackList():
                <tr>
                    <td style="border-bottom: 1px solid #5294CC;">
                        <table>
                            <tr>
                                <td>
                                    <a href="${urlHandlers.UHTrackModMoveUp.getURL(track)}">
                                        <img border="0" src="${Config.getInstance().getSystemIconURL("upArrow")}" alt="">
                                    </a>
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    <a href="${urlHandlers.UHTrackModMoveDown.getURL(track)}">
                                        <img border="0" src="${Config.getInstance().getSystemIconURL("downArrow")}" alt="">
                                    </a>
                                </td>
                            </tr>
                        </table>
                    </td>
                    <td style="border-bottom: 1px solid #5294CC;">
                        <input type="checkbox" name="selTracks" value="${track.getId()}">
                    </td>
                    <td align="left" style="border-bottom: 1px solid #5294CC;">${track.getCode()}</td>
                    <td align="left" width="30%%" style="border-bottom: 1px solid #5294CC;">
                        <a href="${urlHandlers.UHTrackModification.getURL(track)}">${track.getTitle()}</a>
                    </td>
                    <td align="left" width="70%%" style="border-bottom: 1px solid #5294CC;">${track.getDescription()}</td>
                </tr>
            % endfor

            </table>
            % endif

        </td>
    </tr>
    <tr>
        <td class="buttonsSeparator" align="center" width="100%">
            <table align="center">
                <tr>
                    <td align="center">
                            <input type="submit" class="btn" value="${ _("Remove Selected")}">
                        </form>
                    </td>
                    <td>
                        <form action="${ addTrackURL }" method="POST">
                            <input type="submit" class="btn" value="${ _("Add Track")}">
                        </form>
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
<br>
<script type="text/javascript">
$('#inPlaceEditDescription').html(new ParsedRichTextInlineEditWidget('event.program.changeDescription', ${ jsonEncode(dict(conference="%s"%conf.getId())) }, ${jsonEncode(conf.getProgramDescription())}, null, null, "${_('No description')}").draw().dom);
</script>