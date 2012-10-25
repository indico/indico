<script type="text/javascript">
    include(ScriptRoot + "indico/Timetable/Loader.js");

    $(function(){
        var resultCache = [];
        var allItems = $(".speakerIndexItem");

        $("#filterSpeakers").keyup(function(){
            var searchString = $("#filterSpeakers").attr('value');
            allItems.css('visibility', 'hidden');
            allItems.addClass('specialHide');
            if (resultCache[searchString] == undefined) {
                var items = $(".speakerIndexItemText:contains('"+ searchString +"')").parent().parent();
                resultCache[searchString] = items;
            } else {
                var items = resultCache[searchString];
            }
            items.css('visibility', '');
            items.removeClass('specialHide');
            $("#numberFiltered").text(items.length);
            items.length == 1 ? $("#numberFilteredText").text($T("speaker")) : $("#numberFilteredText").text($T("speakers"));
        });
     });
</script>
<div class="speakerIndexFiltersContainer">
    <div>
        <input type="text" id="filterSpeakers" value="" placeholder="${ _('Search in speakers') }">
    </div>
    <div class="speakerIndexFilteredText">
        ${_("Displaying ")}<span style="font-weight:bold;" id="numberFiltered">${len(items)}</span>
        <span id="numberFilteredText">${ _("speaker") if len(items) == 1 else _("speakers")}</span>
        ${_("out of")}
        <span style="font-weight:bold;">${len(items)}</span>
    </div>
</div>
<div class="speakerIndex">
    % for key, item in items.iteritems():
        <div class="speakerIndexItem">
            <div style="padding-bottom: 10px">
                <span class="speakerIndexItemText">${item[0]['fullName']}</span>
                % if item[0]['affiliation']:
                    <span style="color: #888">(${item[0]['affiliation']})</span>
                % endif
            </div>
            % for i in range(1, len(item)):
                <div class="contribItem">
                    <a href="${item[i]['url']}">${item[i]['title']}</a>
                    % if item[i]['materials']:
                        <img id="materialMenuIcon${key}${i}" title="${_('materials')}" src="./images/material_folder.png" width=12 height=12 style="cursor: pointer;"/>
                    % endif
                </div>
            % endfor
        </div>
    % endfor
</div>
