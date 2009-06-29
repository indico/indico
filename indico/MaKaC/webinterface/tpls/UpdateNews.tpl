<div id="newsToolBar" class="newsToolBar"></div>
<div id="newsContainer" class="newsContainer"></div>

<script type="text/javascript">
<!--
    var newsList = new NewsList(<%= jsonEncode(newslist).replace('%','%%') %>, 'newsContainer', <%= jsonEncode(newsTypesList) %>);

    var addButton = Widget.link(command(function(){
                                            newsList.addItem();
    },IndicoUI.Buttons.addButton()));
    $E("newsToolBar").set(addButton);
-->
</script>

