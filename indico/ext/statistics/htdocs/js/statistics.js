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
                      'startDate' : $('#startDate').val(),
                      'endDate' : $('#endDate').val(),
                      'tab' : 'Piwik'
        };

        var updateContrib = $('#updateContribution').val();

        if (updateContrib != 'None') {
            params['contribId'] = updateContrib;
        }

        var uri = '';

        $.each(params, function(key, value) {
            uri += key + '=' + value + '&';
        });

        return uri;
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
