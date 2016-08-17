(function(global) {
    'use strict';

    // TODO: Add plugin i18n
    var $t = $T;

    global.eventManageVCRooms = function() {

        $('.js-create-room:not([data-vc-system])').ajaxDialog({
            title: $T('Video services'),
            hidePageHeader: true
        });

        $('#btn-add-existing').ajaxDialog({
            onClose: function(data) {
                if (data) {
                    location.reload();
                }
            }
        });

        $('.js-vcroom-remove').on('click', function(e) {
            e.preventDefault();
            var $this = $(this);

            var msg = $t('Do you really want to remove this videoconference room from the event?');
            if ($this.data('numEvents') == 1) {
                msg += ' ' + $t('Since it is only used in this event, it will be deleted from the server, too!');
                confirmPrompt(msg).then(function() {
                     var csrf = $('<input>', {type: 'hidden', name: 'csrf_token', value: $('#csrf-token').attr('content')});
                     $('<form>', {
                        action: $this.data('href'),
                        method: 'post'
                     }).append(csrf).appendTo('body').submit();
                 });
            } else {
                new SpecialRemovePopup($T("Videoconference room removal"),
                                       $T('This video conference room is used in {0} Indico events.<br> Do you want to remove this videoconference from <strong>All</strong> {0} events  or just this <strong>One</strong>?').format($this.data('numEvents')),
                    function(action) {
                        var csrf = $('<input>', {type: 'hidden', name: 'csrf_token', value: $('#csrf-token').attr('content')});
                        if (action === 1) {
                             $('<form>', {
                                action: $this.data('href'),
                                method: 'post'
                            }).append(csrf).appendTo('body').submit();
                        } else if (action === 2) {
                             $('<form>', {
                                action: build_url($this.data('href'),{delete_all: '1'}),
                                method: 'post'
                            }).append(csrf).appendTo('body').submit();
                        }
                    }, $T("Delete One"), $T("Delete All")).open();


            }
        });

        $('.js-vcroom-refresh').on('click', function(e) {
            e.preventDefault();
            var $this = $(this);
            var csrf = $('<input>', {type: 'hidden', name: 'csrf_token', value: $('#csrf-token').attr('content')});
            $('<form>', {
                action: $this.data('href'),
                method: 'post'
            }).append(csrf).appendTo('body').submit();
        });

        $('.vc-room-entry.deleted').qtip({
            content: $T('This room has been deleted and cannot be used. \
                         You can detach it from the event, however.'),
            position: {
                my: 'top center',
                at: 'bottom center'
            }
        });

        $('.toggle-details').on('click', function(e) {
            e.preventDefault();
            var $this = $(this);

            if ($this.closest('.vc-room-entry.deleted').length) {
                return;
            }

            $this.closest('tr').next('tr').find('.details-container').slideToggle({
                start: function() {
                    $this.toggleClass('icon-next icon-expand');
                }
            });
        }).filter('.vc-room-entry:not(.deleted) .toggle-details')
          .qtip({content: $T('Click to toggle collapse status')});

        $('.toggle .i-button').on('click', function(){
            var toggle = $(this);
            toggle.toggleClass('icon-eye icon-eye-blocked');
            var $input = toggle.siblings('input');
            $input.prop('type', $input.prop('type') === 'text' ? 'password' : 'text');
        });
    };

})(window);
