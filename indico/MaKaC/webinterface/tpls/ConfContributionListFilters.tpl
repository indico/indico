<%block name="staticURL">
    <div id="staticURLContainer" style="display:none">
        <div id="staticURLContent">
            <div>${ _("You can use this link for bookmarks:")}</div>
            <input readonly="readonly" type="text" id="staticURL" style="width: 100%;" name="staticURL" />
            <div class="staticURLNote">${_('Please use <strong>CTRL + C</strong> to copy this URL')}</div>
        </div>
    </div>
</%block>

<%block name="listToPDF">
    <form action="${str(urlHandlers.UHContributionListToPDF.getURL(conf))}" id="formContrib" method="post" target="_blank"></form>
</%block>

<div class="contributionListFiltersContainer">
    <%block name="filterHeader">
        <div>
          <input type="text" id="filterContribs" value="${filterText}" placeholder="${ _("Search in contributions") }">
          <div id="resetFiltersContainer" style="display:none"><a class="fakeLink" style="color: #881122" id="resetFilters">${_("Reset filters")}</a> |</div>
          <a class="fakeLink" id="showFilters">${_("More filters")}</a> |
          <a class="fakeLink" id="staticURLLink">${ _("Static URL for this result")}</a> |
          <a class="fakeLink" id="exportPDF">${ _("Export to PDF")}</a>
        </div>
    </%block>
    <div id="filterContent" class="CRLDiv" style="display:none">

        <%block name="filterSession">
            % if len(conf.getSessionListSorted()) > 0:
                <select id="sessionSelector" name="sessionSelector" multiple="multiple">
                    <option value="-1" ${'selected="selected"' if not filterCriteria or filterCriteria.getField("session").getShowNoValue() else ""}>--${_("not specified")}--</option>
                    % for session in conf.getSessionListSorted():
                        <option value="${session.getId()}" ${'selected="selected"' if not filterCriteria or (session.getId() in filterCriteria.getField("session").getValues()) else ""}>
                            ${session.getTitle()}
                        </option>
                    % endfor
                </select>
            % endif
        </%block>

        <%block name="filterTrack">
            % if len(conf.getTrackList()) > 0:
                <select id="trackSelector" name="trackSelector" multiple="multiple">
                    <option value="-1" ${'selected="selected"' if not filterCriteria or filterCriteria.getField("track").getShowNoValue() else ""}>--${_("not specified")}--</option>
                    % for track in conf.getTrackList():
                        <option value="${track.getId()}" ${'selected="selected"' if not filterCriteria or (track.getId() in filterCriteria.getField("track").getValues()) else ""}>
                            ${track.getTitle()}
                        </option>
                    % endfor
                </select>
            % endif
        </%block>

        <%block name="filterType">
            % if len(conf.getContribTypeList()) > 0:
                <select id="contribTypeSelector" name="contribTypeSelector" multiple="multiple">
                    <option value="-1" ${'selected="selected"' if not filterCriteria or filterCriteria.getField("type").getShowNoValue() else ""}>--${_("not specified")}--</option>
                    % for type in conf.getContribTypeList():
                        <option value="${type.getId()}" ${'selected="selected"' if not filterCriteria or (type.getId() in filterCriteria.getField("type").getValues()) else ""}>
                            ${type.getName()}
                        </option>
                    % endfor
                </select>
            % endif
        </%block>
    </div>
    <%block name="filterTextInput">
        <div class="contributionListFilteredText">
            ${_("Displaying ")}<span style="font-weight:bold;" id="numberFiltered">${len(contributions)}</span>
            <span id="numberFilteredText">${ _("contribution") if len(contributions) == 1 else _("contributions")}</span>
            ${_("out of")}
            <span style="font-weight:bold;">${len(contributions)}</span>
        </div>
    </%block>
</div>

<%block name="scripts">
    <script type="text/javascript">

    var resultCache = [];
    var allItems = $(".contributionListContribItem");

    var verifyFilters = function(){
        $(".contributionListContribItem").hide();
        var selector= [];

        var term = $("#filterContribs").val();
        allItems.css('display', 'none');
        var items;
        if (resultCache[term] == undefined) {
            items = $(".contributionListContribItem").textContains(term);
            resultCache[term] = items;
        } else {
            items = resultCache[term];
        }

        % if len(conf.getContribTypeList()) > 0:
            $("#contribTypeSelector").multiselect("getChecked").each(function(index) {
                selector.push("[data-type="+ this.value +"]");
            });
            items = items.filter(selector.join(', '));
        % endif

        <%block name="sessionScript">
            % if len(conf.getSessionListSorted()) > 0:
                selector = [];
                $("#sessionSelector").multiselect("getChecked").each(function(index) {
                    selector.push("[data-session="+ this.value +"]");
                });
                items = items.filter(selector.join(', '));
            % endif
        </%block>

        % if len(conf.getTrackList()) > 0:
            selector =[];
            $("#trackSelector").multiselect("getChecked").each(function(index) {
                selector.push("[data-track="+ this.value +"]");
            });
            items = items.filter(selector.join(', '));
        % endif

        items.css('display', 'block');
        $("#numberFiltered").text(items.length);
        if(items.length == 1) {
            $("#numberFilteredText").text($T("contribution"));
        } else {
            $("#numberFilteredText").text($T("contributions"));
        }
        updateStaticURL();
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

    var updateStaticURL = function() {
        var url = '${ urlHandlers.UHContributionList.getURL(conf) }?';
        var query = checkQueryParam($("#contribTypeSelector"), "typeShowNoValue", "selTypes")
                + checkQueryParam($("#sessionSelector"), "sessionShowNoValue", "selSessions")
                + checkQueryParam($("#trackSelector"), "trackShowNoValue", "selTracks");
        if (query !=""){
            query = "&filter=yes" + query;
        }
        var term = $("#filterContribs").val();
        if(term != ""){
            query += "&filterText=" + term;
        }
        url += query;
        $('#staticURL').val(url);
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

    $(function(){
        createMultiselect($("#contribTypeSelector"), "contribution types");

        <%block name="sessionSelectorName">
            createMultiselect($("#sessionSelector"), "sessions");
        </%block>

        createMultiselect($("#trackSelector"), "tracks");

        $("#showFilters").click(function(){
            if($("#filterContent").is(':hidden')){
                $("#showFilters").text('Hide filters');
                $("#filterContent").show("blind");
            } else {
                $("#showFilters").text('More filters');
                $("#filterContent").hide("blind");
            }
        });

        $("#resetFilters").click(function(){
            $("#filterContribs").val('');
            $("#contribTypeSelector, #sessionSelector , #trackSelector").multiselect("checkAll");
            verifyFilters();
            $("#resetFiltersContainer").hide();
        });

        $("#filterContribs").keyup(function(){
            verifyFiltersAndReset();
        });

        $("#formContrib").submit(
            function(){
                if($("div.contributionListContribItem:visible").length > 0){
                    $("div.contributionListContribItem:visible").each(function(){
                        $('<input />').attr('type', 'hidden')
                        .attr('name', "contributions")
                        .val($(this).data("id"))
                        .appendTo('#formContrib');
                    });
                    return true;
                } else{
                    new WarningPopup($T("Warning"), $T("No contribution displayed!")).open();
                    return false;
                }
        });
        $("#exportPDF").click(function(){
            $("#formContrib").submit();
        });

        $('#staticURLLink').qtip({
            content: {
                text: function() { return $('#staticURLContainer'); }
            },
            position: {
                my: 'bottom middle',
                at: 'top middle'
            },
            show: {
                event: 'click'
            },
            hide: {
                event: 'unfocus',
                fixed: true,
                effect: function() {
                    $(this).fadeOut(300);
                }
            },
            style: {
                width: 'auto',
                classes: 'qtip-rounded qtip-shadow qtip-blue'
            }
        },{
            beforeRender: updateStaticURL()
        });

        $('body').delegate('#staticURL', 'click', function(e){
            $(this).select();
        });

        if(verifyFilters()){
            $("#showFilters").text('Hide filters');
            $("#filterContent").show("blind");
            $("#resetFiltersContainer").css("display", "inline");
        }

     });
    </script>
</%block>
