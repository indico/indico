$(function zeroclipboardInit() {
    'use strict';

    // check if ZeroClipboard is loaded and if the HTML init class is defined
    if (!window.ZeroClipboard || !$('.zeroclipboard-init').length) { return; }

    ZeroClipboard.config({'swfPath': Indico.Urls.Base + '/js/lib/zeroclipboard/ZeroClipboard.swf'});

    // register i-has-action-clip ZeroClipboard handling
    var $iHasAction = $('.i-has-action.i-has-action-clip > .i-button');
    if ($iHasAction.length) {
        ZeroClipboard.on('ready', function() {
            var client = new ZeroClipboard($iHasAction);
            client.on('error', function() { client.destroy(); });

            client.on('ready', function() {
                client.on('copy', function(event) {
                    event.clipboardData.setData('text/plain', $(event.target).siblings('input').val());
                });
                client.on('aftercopy', function(event) {
                    $(event.target).parent().siblings('.i-has-action-message')
                        .css('visibility', 'visible')
                        .fadeTo(50, 1)
                        .fadeTo(1500, 0)
                        .animate({'visibility': 'hidden'}, 0); // animate to have css queued after fadeOut
                });
            });
        });
    }

    $(document).one('mouseover', '.zeroclipboard-init', function loadZeroClipBoardFlash() {
        ZeroClipboard.create(); // loads the Flash file
    });
});
