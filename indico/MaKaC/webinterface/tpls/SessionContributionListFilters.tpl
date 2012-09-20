
<div class="contributionListFiltersContainer">
    <div>
        <input type="text" id="filterContribs" value="" placeholder=${ _("Search in contributions") }>
        <div id="resetFiltersContainer" style="display:none"><a class="fakeLink" style="color: #881122">${_("Reset filter")}</a></div>
    </div>
    <div id="filterContent" class="CRLDiv">
        % if len(session.getSlotList()) > 0:
            <select id="slotSelector" name="slotSelector" multiple="multiple">
                <option value="-1" selected="">--${_("not specified")}--</option>
                % for slot in session.getSlotList():
                    <option value="${slot.getId()}" selected="">
                        ${slot.getFullTitle()}
                    </option>
                % endfor
            </select>

        % endif
    </div>
    <div class="contributionListFilteredText">
        ${_("Displaying ")}<span style="font-weight:bold;" id="numberFiltered">${len(session.getContributionList())}</span>
        <span id="numberFilteredText">${ _("contribution") if len(session.getContributionList()) == 1 else _("contributions")}</span>
        ${_("out of")}
        <span style="font-weight:bold;">${len(session.getContributionList())}</span>

    </div>
</div>

<script type="text/javascript">
var verifyFilters = function(){
    $(".contributionListContribItem").hide();
    var selector= [];
    var term = $("#filterContribs").attr('value');

    var items = $(".contributionListContribItem:contains('"+ term +"')");

    % if len(session.getSlotList()) > 0:
        selector =[];
        $("#slotSelector").multiselect("getChecked").each(function(index) {
            selector.push("[data-type="+ this.value +"]");
        });
        items = items.filter(selector.join(', '));
    % endif

    items.show();
    $("#numberFiltered").text(items.length);
    if(items.length == 1) {
        $("#numberFilteredText").text($T("contribution"));
    } else {
        $("#numberFilteredText").text($T("contributions"));
    }
    return (items.length !=  $(".contributionListContribItem").length);
};

var verifyFiltersAndReset = function(){
    if(verifyFilters()){
        $("#resetFiltersContainer").css("display", "inline");
    } else {
        $("#resetFiltersContainer").hide();
    }
};

var checkQueryParam = function(place, noSpecified, queryText){
    var query = "";
    place.multiselect("getChecked").each(function(index) {
        if(this.value == -1){
            query += "&" + noSpecified +"=1";
        } else {
            query += "&"+ queryText + "=" + this.value;
        }
    });
    return query;
};

var createMultiselect = function(place, kind){
    place.multiselect({
        selectedText: function(numChecked, numTotal, checkedItems){
            return numChecked + " "+ kind + " selected";
         },
        noneSelectedText: "Select " + kind,
        checkAllText: "All",
        uncheckAllText: "None",
        checkAll: function(e){verifyFiltersAndReset();},
        uncheckAll: function(e){verifyFiltersAndReset();},
        click: function(e){verifyFiltersAndReset();},
        classes: 'ui-multiselect-widget'
      });
};

IndicoUI.executeOnLoad(function(){
    createMultiselect($("#slotSelector"), "slots");

    $("#resetFilters").click(function(){
        $("#filterContribs").attr("value","");
        $("#slotSelector").multiselect("checkAll");
        verifyFilters();
        $("#resetFiltersContainer").hide();
    });

    $("#filterContribs").keyup(function(){
        verifyFiltersAndReset();
    });

    if(verifyFilters()){
        $("#resetFiltersContainer").css("display", "inline");
    }

 });
</script>