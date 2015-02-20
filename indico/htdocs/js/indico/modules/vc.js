(function(global) {
    'use strict';

    // TODO: Add plugin i18n
    var $t = $T;

    global.eventManageVCRooms = function() {
        $('.js-vcroom-remove').on('click', function(e) {
            e.preventDefault();
            var $this = $(this);
            var msg = $t('Do you really want to remove this video-conferencing room from the event?');
            if ($this.data('numEvents') == 1) {
                msg += ' ' + $t('Since it is only used in this event, it will be deleted from the server, too!');
            }
            new ConfirmPopup($t('Delete this Vidyo Room?'), msg, function(confirmed) {
                if (!confirmed) {
                    return;
                }

                $('<form>', {
                    action: $this.data('href'),
                    method: 'post'
                }).appendTo('body').submit();
            }).open();
        });

        $('.js-vcroom-refresh').on('click', function(e) {
            e.preventDefault();
            var $this = $(this);
            $('<form>', {
                action: $this.data('href'),
                method: 'post'
            }).appendTo('body').submit();
        });
    };
})(window);
