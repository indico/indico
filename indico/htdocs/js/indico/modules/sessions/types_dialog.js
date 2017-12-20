(function(global) {
    'use strict';

    global.setupSessionTypesDialog = function setupSessionTypesDialog() {
        var $manageSessionTypes = $('.manage-session-types');

        /* Set the customData to true indicating that the session list needs to be refreshed */
        function dialogModified() {
            $manageSessionTypes.trigger('ajaxDialog:setData', [true]);
        }

        $('.manage-session-types table').tablesorter({
            sortList: [[0, 0]],
            headers: {
                2: {
                    sorter: false
                }
            }
        });

        $('.js-new-session-type').on('ajaxDialog:closed', function(evt, data) {
            evt.preventDefault();
            if (data) {
                var $lastRow = $('.manage-session-types table tr:last');
                if ($lastRow.length) {
                    $lastRow.after(data.html_row);
                } else {
                    $manageSessionTypes.trigger('ajaxDialog:reload');
                }
            }
        });

        $manageSessionTypes.on('ajaxDialog:closed', '.js-edit-session-type', function(evt, data) {
            evt.preventDefault();
            var $row = $(this).closest('tr');
            if (data) {
                $row.replaceWith(data.html_row);
                dialogModified();
            }
        });

        $manageSessionTypes.on('indico:confirmed', '.js-delete-session-type', function(evt) {
            evt.preventDefault();
            var $this = $(this);
            var $row = $this.closest('tr');
            $.ajax({
                url: $this.data('href'),
                method: $this.data('method'),
                complete: IndicoUI.Dialogs.Util.progress(),
                error: handleAjaxError,
                success: function() {
                    $row.remove();
                    dialogModified();
                    if ($('.manage-session-types table tbody tr').length === 0) {
                        $manageSessionTypes.trigger('ajaxDialog:reload');
                    }
                }
            });
        });
    };
})(window);
