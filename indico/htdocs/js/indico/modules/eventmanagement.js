(function(global) {
    'use strict';

    global.setupEventPersonsList = function setupEventPersonsList() {
        enableIfChecked('#persons-list', '.select-row:visible', '#persons-list .js-requires-selected-row');
        $('#persons-list [data-toggle=dropdown]').closest('.group').dropdown();

        $('#persons-list [data-filter]').on('click', function() {
            var personRows = $('#persons-list tr[data-person-roles]');
            var filters = $('#persons-list [data-filter]:checked').map(function() {
                return $(this).data('filter');
            }).get();

            var visibleEntries = personRows.filter(function() {
                var $this = $(this);

                return _.any(filters, function(filterName) {
                    return $this.data('person-roles')[filterName];
                });
            });

            personRows.hide();
            visibleEntries.show();
            $('#persons-list').trigger('indico:syncEnableIfChecked');
        });

        $('#persons-list td').on('mouseenter', function() {
            var $this = $(this);
            if (this.offsetWidth < this.scrollWidth && !$this.attr('title')) {
                $this.attr('title', $this.text());
            }
        });

        $('#persons-list .tablesorter').tablesorter({
            cssAsc: 'header-sort-asc',
            cssDesc: 'header-sort-desc',
            headerTemplate: '',
            sortList: [[1, 0]]
        });
    };
})(window);
