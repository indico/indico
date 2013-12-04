// Drag and drop for the authors
$('#sortspace').tablesorter({

    onDropFail: function() {
        var popup = new AlertPopup($T('Warning'), $T('You cannot move the author to this list because there is already an author with the same email address.'));
        popup.open();
    },
    canDrop: function(sortable, element) {
        if (sortable.attr('id') == 'inPlacePrAuthors') {
            return authorsManager.canDropElement('pr', element.attr('id'));
        } else if (sortable.attr('id') == 'inPlaceCoAuthors') {
            return authorsManager.canDropElement('co', element.attr('id'));
        }
        return false;
    },
    onUpdate: function() {
        authorsManager.updatePositions();
        authorsManager.checkPrAuthorsList();
        return;
    },
    sortables: '.sortblock ul', // relative to element
    sortableElements: '> li', // relative to sortable
    handle: '.authorTable', // relative to sortable element - the handle to start sorting
    placeholderHTML: '<li></li>' // the html to put inside the placeholder element
});

// Pagedown editor stuff


function block_handler(text, rbg) {
    return text.replace(/^ {0,3}""" *\n((?:.*?\n)+?) {0,3}""" *$/gm, function (whole, inner) {
        return "<blockquote>" + rbg(inner) + "</blockquote>\n";
    });
}

$(function() {
    $('textarea.wmd-input').each(function(i, elem) {
        var fieldId = $(elem).closest('td').data('fieldId');

        converter = Markdown.getSanitizingConverter();
        converter.hooks.chain("preBlockGamut", block_handler);

        var editor = new Markdown.Editor(converter, "-f_" + fieldId);
        PageDownMathJax.mathjaxEditing().prepareWmdForMathJax(editor, "-f_" + fieldId, [["$$", "$$"], ["\\\\(","\\\\)"]]);
        editor.run();
    });

    _(['markdown-info', 'latex-info']).each(function(name) {
        $('.' + name).qtip({
            content: $('#' + name + '-text').html(),
            hide: {
                event: 'unfocus'
            },
            show: {
                solo: true
            },
            style: {
                classes: 'informational'
            }
        }).click(function() {
            return false;
        });
    });
});