<form method="get" action="${searchAction}" id="searchBoxForm" style="margin: 0px;">
<input type="hidden" id="searchCategId" name="categId" value="0" data-current="${targetId}" data-current-name="${categName}"/>
<input type="hidden" name="sortOrder" value="d"/>
<div id="UISearchBox">
    <div id="searchControls">
        <div class="searchButton">

        </div>
        <div id="moreOptions" class="${ moreOptionsClass }" onclick="expandMenu(this);"></div>
        <input style="background-color: transparent;" type="text" id="searchText" name="p" />
</div>

    <div id="extraOptions">
        <div id="advancedOptionsLabel">${ _("Advanced options")} <%block name='searchSyntaxTooltip'></%block></div>
        <table id="extraOptionsTable">
        <tr>
                <td style="text-align: right;">${ _("Search in")}</td>
                <td>
                    <select name="f">
                  <option value="" selected>${ _("Anywhere")}</option>
                  <option value="title">${ _("Title")}</option>
                  <option value="abstract">${ _("Talk description/Abstract")}</option>
                  <option value="author">${ _("Author/Speaker")}</option>
                  <option value="affiliation">${ _("Affiliation")}</option>
                  <!-- >option value="fulltext">${ _("Fulltext")}</option-->
                  <option value="keyword">${ _("Keyword")}</option>
                    </select>
                </td>
            </tr>
            <%block name="searchExtras">
            </%block>
            <tr>
                <td style="text-align: right;">${ _("Start Date")}</td>
                <td>
                    <span id="startDatePlaceBox">
                      <input name="startDate" id="startDate" type="text" />
                    </span>
                </td>
            </tr>
            <tr>
                <td style="text-align: right;">${ _("End Date")}</td>
                <td>
                    <span id="endDatePlaceBox">
                      <input name="endDate" id="endDate" type="text" />
                    </span>
                </td>
            </tr>
        </table>
    </div>
</div>
</form>

<script type="text/javascript">

function expandMenu(domElem)
{
    var elem = new XElement(domElem);

    if(!exists(elem.dom.extraShown))
    {
        $('#extraOptions').width($('#searchControls').width()).slideDown('fast');
        $('#extraOptions').position({
            of: $('#searchControls'),
            my: 'right top',
            at: 'right bottom'
        });
        elem.dom.extraShown=true;
        resetForm();
    }
    else
    {
        $('#extraOptions').slideUp('fast');
        elem.dom.extraShown=null;
        resetForm();

    }
    return false;
}



function resetForm()
{
    // reset all the fields, except the phrase
    var text = $E('searchText').dom.value;
    $E('searchBoxForm').dom.reset();
    $E('searchText').dom.value = text;

}

function verifyForm()
{
    var startDate = $('#startDate').val();
    var endDate = $('#endDate').val();
    return (!startDate || Util.parseDateTime(startDate, IndicoDateTimeFormats.DefaultHourless)) &&
        (!endDate || Util.parseDateTime(endDate, IndicoDateTimeFormats.DefaultHourless));
}


var searchControls = $E('searchControls');

var intelligentSearchBox = new IntelligentSearchBox({name: 'p', id: 'searchText',
                                 style: {backgroundColor: 'transparent', outline: 'none'}
                 }, $E('UISearchBox'), $E('searchSubmit'));


$(function() {
    $('#startDate').datepicker({ dateFormat: "dd/mm/yy", firstDay:1 });
    $('#endDate').datepicker({ dateFormat: "dd/mm/yy", firstDay:1 });

    $E('searchText').replaceWith(
        intelligentSearchBox.draw()
    );

    var where = $('#searchCategId').data('current');
    var target_title = $('#searchCategId').data('current-name');

    $('.searchButton').click(function() {
        if (verifyForm()) {
            $('#searchBoxForm').submit();
        };
    })

    $('#searchText').keypress(function(e) {
        if(e.which == 13 && !intelligentSearchBox.isAnyItemSelected()){
            if (verifyForm()) {
                $('#searchBoxForm').submit();
            }
        }
    });

    if (where != '0') {
        $('.searchButton', '#searchBoxForm').before($('<div class="searchTag"/>'));
        $('.searchTag').search_tag({
            everywhere: true,
            categ_title: target_title,
            categ_id: where,
            input: $('#searchCategId')
        });
    }
});

</script>
