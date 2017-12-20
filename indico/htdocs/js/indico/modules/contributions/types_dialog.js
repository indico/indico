(function(global) {
    'use strict';

    global.setupContributionTypesDialog = function setupContributionTypesDialog() {
        var $manageContributionTypes = $('.manage-contribution-types');

        /* Set the customData to true indicating that the contribution list needs to be refreshed */
        function dialogModified() {
            $manageContributionTypes.trigger('ajaxDialog:setData', [true]);
        }

        $('.manage-contribution-types table').tablesorter({
            sortList: [[0, 0]],
            headers: {
                2: {
                    sorter: false
                }
            }
        });

        $('.js-new-contribution-type').on('ajaxDialog:closed', function(evt, data) {
            evt.preventDefault();
            if (data) {
                var $lastRow = $('.manage-contribution-types table tr:last');
                if ($lastRow.length) {
                    $lastRow.after(data.html_row);
                } else {
                    $manageContributionTypes.trigger('ajaxDialog:reload');
                }
            }
        });

        $manageContributionTypes.on('ajaxDialog:closed', '.js-edit-contribution-type', function(evt, data) {
            evt.preventDefault();
            var $row = $(this).closest('tr');
            if (data) {
                $row.replaceWith(data.html_row);
                dialogModified();
            }
        });

        $manageContributionTypes.on('indico:confirmed', '.js-delete-contribution-type', function(evt) {
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
                    if ($('.manage-contribution-types table tbody tr').length === 0) {
                        $manageContributionTypes.trigger('ajaxDialog:reload');
                    }
                }
            });
        });
    };
})(window);
