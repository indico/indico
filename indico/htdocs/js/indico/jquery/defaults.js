// Indico-specific settings
$.extend(true, $.cern.daterange.prototype.options, {
    pickerOptions: { dateFormat: 'dd/mm/yy' },
    labelAttrs: { 'class': 'label titleCellFormat' },
    labels: [$T('Choose the start date'), $T('Choose the end date')]
});

$.fn.qtip.defaults = $.extend(true, {}, $.fn.qtip.defaults, {
    position: { my: 'top left', at: 'bottom right', viewport: $(window) },
    style: {tip: {corner: true}}
});

$.extend($.colorbox.settings, {
    opacity: 0.6
});
