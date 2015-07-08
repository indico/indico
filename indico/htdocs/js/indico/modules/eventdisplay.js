$(function() {
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

    $('.js-show-note-toggle').on('click', function(e) {
        if ($(this).is('a')) {
            e.preventDefault();
        }
        // Note for event
        var note = $(this).closest('#event-note-section');
        // Note for other elements
        if (note.length === 0) {
            note = $(this).closest('li').children('.note-area-wrapper');
        }
        content = note.hasClass('togglable') ? note : note.find('.togglable');
        content.slideToggle();
    });

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
