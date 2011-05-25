// Indico-specific settings
(function($) {
    $.extend(true, $.ui.daterange.prototype.options, {
        pickerOptions: { dateFormat: 'dd/mm/yy' },
        labelAttrs: { 'class': 'label titleCellFormat' },
        labels: [$T('Choose the start date'), $T('Choose the end date')]
    });
})(jQuery);
