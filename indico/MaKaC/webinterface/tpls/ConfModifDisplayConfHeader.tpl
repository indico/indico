<a name="tickertape"></a>
<div class="groupItem">

    <table class="groupTable">
        <tr>
            <td colspan="2">
                <div class="groupTitle"> ${ _("Announcement")}</div>
            </td>
        </tr>

        <tr>
            <td nowrap class="dataCaptionTD"><span class="titleCellFormat">${ _("Text announcement")}</span></td>
            <td bgcolor="white" width="65%" class="blacktext">
                <form action=${ tickertapeURL } method="POST" style="margin:0;">
                    <input type="text" size="60" name="ttText" value=${ text }>
                    <input type="submit" class="btn" name="savettText" value="${ _("save")}"> ${ modifiedText }<br>

                    <small> ${ _("""Note that text announcement must be enabled above to display this text""")}</small>
                </form>
            </td>
        </tr>

        <tr>
            <td nowrap class="dataCaptionTD"><span class="titleCellFormat"> ${ _("Status")}</span></td>
            <td bgcolor="white" width="65%" class="blacktext">
                <form action=${ simpleTextURL } method="POST">
                    <b>${ status }</b>
                    <input type="submit"  id="toggleSimpleTextButton" class="btn" value="${ statusBtn }">
                </form>
            </td>
        </tr>
        <tr>
            <td colspan="2">
                <a name="headerFeatures"></a>
                <div class="groupTitle"> ${ _("Conference header features")}</div>
            </td>
        </tr>

        <tr>
            <td nowrap class="dataCaptionTD"><span class="titleCellFormat"> ${ _("Show in header")}</span>
              <br>
              <br>
              <img src=${ enablePic } alt="${ _("Click to disable")}"> <small> ${ _("Enabled announ.")}</small>
              <br>
              <img src=${ disablePic } alt="${ _("Click to enable")}"> <small> ${ _("Disabled announ.")}</small>
            </td>
            <td bgcolor="white" width="65%" class="blacktext">
              <table align="left">
                <tr>
                    <td>
                        <form action=${ nowHappeningURL } method="POST" id="nowHappForm">
                            <a href="#" onclick="$E('nowHappForm').dom.submit();return false;"><img src=${ nowHappeningIcon } alt="${ nowHappeningTextIcon }" class="imglink">&nbsp; ${ _("Now happening...")}</a>
                        </form>
                    </td>
                </tr>
                <tr>
                    <td>
                        <form action=${ searchBoxURL } method="POST" id="dispSearchBoxForm">
                            <a href="#" onclick="$E('dispSearchBoxForm').dom.submit();return false;"><img src=${ searchBoxIcon } alt="${ searchBoxTextIcon }" class="imglink">&nbsp; ${ _("Display search box")}</a>
                        </form>
                    </td>
                </tr>
                % if confType == "conference" :
                <tr>
                    <td>
                        <form action=${ navigationBoxURL } method="POST" id="navBoxForm">
                            <a href="#" onclick="$E('navBoxForm').dom.submit();return false;"><img src=${ navigationBoxIcon } alt="${ navigationBoxTextIcon }" class="imglink">&nbsp; ${ _("Display navigation bar")}</a>
                        </form>
                    </td>
                </tr>
                % endif
              </table>
            </td>
        </tr>
    </table>
</div>
