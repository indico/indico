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


<div id="newsToolBar" class="newsToolBar"></div>
<div id="newsContainer" class="newsContainer"></div>

<script type="text/javascript">
    var newsList = new NewsList(${ newslist | j,n }, 'newsContainer', ${ newsTypesList | j,n });

    var addButton = Widget.link(command(function(){
                                            newsList.addItem();
    },IndicoUI.Buttons.addButton()));
    $E("newsToolBar").set(addButton);


    $E('inPlaceEditRecentDays').set(new InputEditWidget('news.setRecentDays', {}, ${ jsonEncode(recentDays) }, false, null, null, null).draw());
</script>
