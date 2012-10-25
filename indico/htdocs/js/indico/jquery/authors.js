$(function() {
    var resultCache = [];
    var allItems = $(".authorIndexItem");

    $("#filterAuthors").keyup(function(){
        var searchString = $("#filterAuthors").attr('value');

        allItems.addClass('visibility_hidden');
        if (resultCache[searchString] == undefined) {
            var items = $(".authorIndexItemText:contains('"+ searchString +"')").parent().parent();
            resultCache[searchString] = items;
        } else {
            var items = resultCache[searchString];
        }
        items.removeClass('visibility_hidden')

        $("#numberFiltered").text(items.length);
        $("#numberFilteredText").text(items.length == 1 ? $T("author") : $T("authors"));
    });

    $(".material_icon").each(function() {
        $(this).qtip({
            style: {
                classes: 'material_tip',
            },
            content: {
                text: $(this).siblings('.material_list')
            },
            show: {
                event: 'click'
            },
            hide: {
                event: 'unfocus'
            },
            position: {
                my: 'top right',
                at: 'bottom left'
            }
        });
    });
});
