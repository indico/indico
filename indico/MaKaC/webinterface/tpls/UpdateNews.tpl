<div class="newsContainer">
    <table>
        <tr>
            <td class="dataCaptionTD">
                <span class="dataCaptionFormat" style="white-space: nowrap;">
                    ${ _("Days to keep 'New' tag on recent news items:")}
                </span>
            </td>
            <td class="blacktext">
                <span id="inPlaceEditRecentDays">
                    ${ recentDays }
                </span>
            </td>
        </tr>
    </table>
</div>


<div id="news-toolbar" class="news-toolbar"></div>
<div id="news-container" class="news-container"></div>

<script type="text/javascript">
    var newsList = new NewsList(${ newslist | j,n }, 'news-container', ${ newsTypesList | j,n });

    var addButton = Widget.link(command(function(){
                                            newsList.addItem();
    },IndicoUI.Buttons.addButton()));
    $E("news-toolbar").set(addButton);


    $E('inPlaceEditRecentDays').set(new InputEditWidget('news.setRecentDays', {}, ${ jsonEncode(recentDays) }, false, null, null, null).draw());
</script>
