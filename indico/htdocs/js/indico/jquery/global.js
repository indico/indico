// Global scripts that should be executed on all pages

$(document).ready(function() {
    // Create static tabs. They just load the target URL and use no ajax whatsoever
    $('.static-tabs').each(function() {
        var tabCtrl = $(this);
        tabCtrl.tabs({
            selected: tabCtrl.data('active')
        });
        // Turn tabs into plain links and fix urls (needed for the active tab)
        $('> .ui-tabs-nav a', this).each(function() {
            var $this = $(this);
            $this.attr('href', $this.data('href'));
            $this.unbind('click.tabs');
        });
    });

    // Use qtip for context help
    $('.contextHelp[title]').qtip();
    $('.contextHelp[data-src]').qtip({
        content: {
            text: function() {
                return $($(this).data('src')).removeClass('tip');
            }
        }
    });

    // Enable colorbox for links with rel="lightbox"
    $('a[rel="lightbox"]').colorbox();
});
