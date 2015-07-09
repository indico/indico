$(document).ready(function() {
    'use strict';

    $('.event-service-row > .trigger').click(function() {
        var toggler = $(this);
        toggler.siblings('.event-service-details').slideToggle({
            start: function() {
                toggler.toggleClass('icon-expand icon-collapse');
            },
            duration: 'fast'
        });
    });

    $('.event-service-row-toggle').on('click', function(e) {
        e.preventDefault();
        var toggler = $(this);
        var toggler_button = $(this).parent().siblings('.trigger');
        toggler.parent().siblings('.event-service-details').slideToggle({
            start: function() {
                toggler_button.toggleClass('icon-expand icon-collapse');
            },
            duration: 'fast'
        });
    });

    function toggleNote(element, visible, immediate) {
        // Note for event
        var note = element.closest('#event-note-section');
        // Note for other elements
        if (note.length === 0) {
            note = element.closest('li').children('.note-area-wrapper');
        }
        var content = note.hasClass('togglable') ? note : note.find('.togglable');
        if (immediate) {
            content.toggle(visible);
        } else {
            content[visible === undefined ? 'slideToggle' : visible ? 'slideDown' : 'slideUp']();
        }
    }

    $('a.js-show-note-toggle').on('click', function(e) {
        e.preventDefault();
        toggleNote($(this));
    });

    $('input.js-toggle-note-cb').on('change', function(e, immediate) {
        toggleNote($(this), this.checked, immediate);
    });

    $('input.js-toggle-note-cb').trigger('change', [true]);

    $('.js-note-editor').ajaxDialog({
        title: $T("Edit minutes"),
        confirmCloseUnsaved: true,
        onClose: function(data) {
            if (data) {
                location.reload();
            }
        }
    });
});
