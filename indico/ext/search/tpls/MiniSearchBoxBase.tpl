<div id="UIMiniSearchBox" class="confSearchBox">
<form class="UIForm" method="GET" action="${ searchAction }" id="searchBoxForm" style="margin: 0; padding: 0;">
    <input class="searchButton" type="submit" value="${ _('Search') }" />
    <input type="text" id="searchText" name="p" class="searchField" />
    <input type="hidden" name="confId" value="${ targetId }"/>
    <%block name="searchExtras">
    </%block>
</form>
</div>
