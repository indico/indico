// Indico-specific settings
(function($) {
    $.extend(true, $.ui.daterange.prototype.options, {
        pickerOptions: { dateFormat: 'dd/mm/yy' },
        labelAttrs: { className: 'titleCellFormat' },
        labels: [$T('Choose the start date'), $T('Choose the end date')]
    });
})(jQuery);
