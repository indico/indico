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
});
