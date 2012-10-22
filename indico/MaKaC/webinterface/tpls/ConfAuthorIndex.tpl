<script type="text/javascript">
    include(ScriptRoot + "indico/Timetable/Loader.js");

    $(function(){
        var resultCache = [];
        var allItems = $(".authorIndexItem");

        $("#filterAuthors").keyup(function(){
            var searchString = $("#filterAuthors").attr('value');
            allItems.css('visibility', 'hidden');
            allItems.addClass('specialHide');
            if (resultCache[searchString] == undefined) {
                var items = $(".authorIndexItemText:contains('"+ searchString +"')").parent().parent();
                resultCache[searchString] = items;
            } else {
                var items = resultCache[searchString];
            }
            items.css('visibility', '');
            items.removeClass('specialHide');
            $("#numberFiltered").text(items.length);
            items.length == 1 ? $("#numberFilteredText").text($T("author")) : $("#numberFilteredText").text($T("authors"));
        });
     });
</script>
<div class="authorIndexFiltersContainer">
    <div>
        <input type="text" id="filterAuthors" value="" placeholder="${ _('Search in authors') }">
    </div>
    <div class="authorIndexFilteredText">
        ${_("Displaying ")}<span style="font-weight:bold;" id="numberFiltered">${len(items)}</span>
        <span id="numberFilteredText">${ _("author") if len(items) == 1 else _("authors")}</span>
        ${_("out of")}
        <span style="font-weight:bold;">${len(items)}</span>
    </div>
</div>
<div class="authorIndex">
    % for key, item in items.iteritems():
        <div class="authorIndexItem">
            <div style="padding-bottom: 10px">
                <a class="authorIndexItemText" href="${item[0]['authorURL']}">${item[0]['fullName']}</a>
                % if item[0]['affiliation']:
                    <span style="color: #888">(${item[0]['affiliation']})</span>
                % endif
            </div>
            % for i in range(1, len(item)):
                <div class="contribItem">
                    <a href="${item[i]['url']}">${item[i]['title']}</a>
                    % if item[i]['materials']:
                        <img id="materialMenuIcon${key}${i}" title="${_('materials')}" src="./images/material_folder.png" width=12 height=12 style="cursor: pointer;"/>
                        <script type="text/javascript">
                        $("#materialMenuIcon${key}${i}").click(function() {
                            var timetable = new TimetableBlockBase();
                            timetable.createMaterialMenuQtip($(this), ${item[i]['materials']});
                            $(this).qtip().show();
                        });
                        </script>
                    % endif
                </div>
            % endfor
        </div>
    % endfor
</div>
