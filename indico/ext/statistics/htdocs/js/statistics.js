$(function() {
    $('#statsModify').click(function() {
        var text = ($(this).html() == str_modif_query)
                 ? str_hide_query : str_modif_query;
        $(this).html(text);
        $('#statsFilter').slideToggle('fast');
    });

    $('.statsDates').datepicker({
        dateFormat : 'yy-mm-dd',
        defaultDate : $(this).attr('data-default')
    });

    var buildURI = function() {
        var params = {'confId' : $('#confId').val(),
                      'startDate' : $('#statsFilterStartDate').val(),
                      'endDate' : $('#statsFilterEndDate').val(),
                      'tab' : 'Piwik'
        };

        var updateContrib = $('#updateContribution').val();

        if (updateContrib != 'None') {
            params['contribId'] = updateContrib;
        }

        return $.param(params);
    };

    $('#updateQuery').click(function() {
        var url = 'statistics?';
        url += buildURI();
        window.location.href = url;
    });

    $('#visitsInfoHelp').qtip({
        content: $('#statsInfoHidden').html(),
        position: {
            my: 'top middle',
            at: 'bottom middle'
        },
        style: {
            classes: 'ui-tooltip-rounded ui-tooltip-shadow ui-tooltip-light'
        }
    });
});
