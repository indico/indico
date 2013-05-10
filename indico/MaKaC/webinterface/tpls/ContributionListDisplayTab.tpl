<%doc>
    This is different from ConfContributionListFilters due to only requiring a subset
    of what is present, namely text filter alone.
</%doc>

<div class="contributionListFiltersContainer">
        <input type="text" id="filterContribs" value="" placeholder='${_("Search in contributions")}' />
        <div id="resetFiltersContainer" style="display:none">
            <a class="fakeLink" style="color: #881122" id="resetFilters">${_("Reset filters")}</a>
        </div>
</div>

<div id="contributionList">
    % for contrib in contributions:
        % if contrib.canAccess(accessWrapper):
            <%include file="ConfContributionListContribFull.tpl" args="contrib=contrib,poster=posterSession"/>
        % elif contrib.canView(accessWrapper):
            <%include file="ConfContributionListContribMin.tpl" args="contrib=contrib,poster=posterSession"/>
        % endif
    % endfor
</div>

<script type="text/javascript">
var verifyFilters = function() {
    $(".contributionListContribItem").hide();
    var term = $("#filterContribs").val();
    var items = $(".contributionListContribItem").textContains(term);

    items.show();

    $("#numberFiltered").text(items.length);
    return (items.length !=  $(".contributionListContribItem").length);
};

var verifyFiltersAndReset = function() {
    if(verifyFilters()){
        $("#resetFiltersContainer").css("display", "inline");
    } else {
        $("#resetFiltersContainer").hide();
    }
};

$(document).ready(function(){
    $("#resetFilters").click(function() {
        $("#filterContribs").val("");
        verifyFiltersAndReset();
    });

    $("#filterContribs").keyup(function() {
        verifyFiltersAndReset();
    });

    if(verifyFilters()) {
        $("#filterContent").show("blind");
        $("#resetFiltersContainer").css("display", "inline");
    }
 });
</script>