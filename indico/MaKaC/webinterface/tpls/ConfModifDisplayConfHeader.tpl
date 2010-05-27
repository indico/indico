<a name="tickertape"></a>
<div class="groupItem">

    <table class="groupTable">
        <tr>
            <td colspan="2">
                <div class="groupTitle"> <%= _("Announcement")%></div>
            </td>
        </tr>

        <tr>
            <td nowrap class="dataCaptionTD"><span class="titleCellFormat"> <%= _("Status")%></span></td>
            <td bgcolor="white" width="65%%" class="blacktext"><b>%(status)s</b>
                <input type="button"  id="toggleSimpleTextButton" class="btn" style="margin-left: 30px;" value="%(statusBtn)s">
                <script type="text/javascript">
                $E('toggleSimpleTextButton').observeClick(function() {
                    window.location = <%= simpleTextURL %>
                });
                </script>
            </td>
        </tr>
        <tr>
            <td nowrap class="dataCaptionTD"><span class="titleCellFormat"><%= _("Text announcement")%></span></td>
            <td bgcolor="white" width="65%%" class="blacktext">
                <form action=%(tickertapeURL)s method="POST" style="margin:0;">
                    <input type="text" size="60" name="ttText" value=%(text)s>
                    <input type="submit" class="btn" name="savettText" value="<%= _("save")%>"> %(modifiedText)s<br>

                    <small> <%= _("""Note that text announcement must be enabled above to display this text""")%></small>
                </form>
            </td>
        </tr>

        <tr>
            <td colspan="2">
                <a name="headerFeatures"></a>
                <div class="groupTitle"> <%= _("Conference header features")%></div>
            </td>
        </tr>

        <tr>
            <td nowrap class="dataCaptionTD"><span class="titleCellFormat"> <%= _("Show in header")%></span>
              <br>
              <br>
              <img src=%(enablePic)s alt="<%= _("Click to disable")%>"> <small> <%= _("Enabled announ.")%></small>
              <br>
              <img src=%(disablePic)s alt="<%= _("Click to enable")%>"> <small> <%= _("Disabled announ.")%></small>
            </td>
            <td bgcolor="white" width="65%%" class="blacktext">
              <table align="left">
                <tr>
                    <td>
                        <a href=%(nowHappeningURL)s><img src=%(nowHappeningIcon)s alt="%(nowHappeningTextIcon)s" class="imglink"></a>&nbsp;<a href=%(nowHappeningURL)s> <%= _("Now happening...")%></a>
                    </td>
                </tr>
                <tr>
                    <td>
                        <a href=%(searchBoxURL)s><img src=%(searchBoxIcon)s alt="%(searchBoxTextIcon)s" class="imglink">&nbsp; <%= _("Display search box")%></a>
                    </td>
                </tr>
                <% if confType == "conference" : %>
                <tr>
                    <td>
                        <a href=%(navigationBoxURL)s><img src=%(navigationBoxIcon)s alt="%(navigationBoxTextIcon)s" class="imglink">&nbsp; <%= _("Display navigation bar")%></a>
                    </td>
                </tr>
                <% end %>
              </table>
            </td>
        </tr>
    </table>
</div>
