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

    /* jqPlot Specifics */

    /**
     * This method extracts the data from the JSON returned via the API into
     * the array format which jqPlot requires. Specifying 'withDate' as true
     * makes each element of the array a key-pair value of date-hits for the
     * renderer jqPlot provides.
     */
    var getArrayValues = function(data, key, withDate) {
        output = [];
        withDate = typeof withDate !== 'undefined' ? withDate : true;

        for (var date in data) {
            hits = data[date];
            value = (withDate) ? [date, hits[key]] : hits[key];
            output.push(value);
        }

        return output;
    };

    /**
     * Clears the DOM element for the graph and then initiates a jqPlot render
     * in the target area.
     *
     * @param source - JSON of dates: {total / unique} hits
     */
    var drawGraph = function(source, replot) {
        var graphDOMElement = 'materialDownloadChart';
        var materialHits = [getArrayValues(source, 'total_hits'),
                            getArrayValues(source, 'unique_hits')];

        var plotOptions = {
            axes: {
                xaxis: {
                    renderer:$.jqplot.DateAxisRenderer,
                    min: reportDates.start,
                    max: reportDates.end
                },
                yaxis: {
                    min: 0
                }
            },
            cursor: {
                show: true,
                zoom: true,
                showTooltip: false
            },
            highlighter: {
                show: true,
                sizeAdjust: 5
            },
            grid: {
                background: '#FFFFFF',
                shadow: false
            },
            series: [{
                lineWidth: 1,
                color: '#CCCCCC'
            }, {
                lineWidth: 1,
                color: '#0B63A5'
            }]
        };

        /* Create the plot here */
        if (replot) {
            $.jqplot(graphDOMElement, materialHits, plotOptions).replot();
        } else {
            $.jqplot(graphDOMElement, materialHits, plotOptions);
        }

    };

    /**
     * Acts as a wrapper around an AJAX indicoRequest and the subsequent call-
     * back to drawGraph().
     */
    var loadGraph = function(uri, replot) {

        replot = typeof replot !== 'undefined' ? replot : false;

        indicoRequest('piwik.getMaterialStatistics',
        {
            startDate: $('#startDate').val(),
            endDate: $('#endDate').val(),
            confId: $('#confId').val(),
            contribId: $('#contribId').val(),
            materialURL: uri
        },
        function(result, error) {
            if (!error) {
                if (result !== null) {
                    drawGraph(result['individual'], replot);
                }
            } else {
                /* Log the issue here */
            }
        });
    };

    /* jqTree Specifics */
    var treeDOMTarget = '#materialTree';

    var drawTree = function(treeData) {
        $(treeDOMTarget).tree(
        {
            data: treeData,
            autoOpen: 0,
            saveState: true,
            onCanSelectNode: function(node) {
                /* If this node has no children, it is material - ergo, make it
                 * selectable so that the event binding can work. */
                return (node.children.length == 0)
            },
            onCreateLi: function(node, $li) {
                if (node.id !== undefined) {
                    $li.find('.title').addClass('selectableNode');
                }
            }
        });
    }

    var loadTree = function() {
        var materialTreeData = null;

        /* Placeholder loading spinner for larger events. */
        $(treeDOMTarget).html(progressIndicator(true, true).dom);

        indicoRequest('piwik.getMaterialTreeData',
        {
            confId: $('#confId').val()
        },
        function(result, error) {
            if (!error) {
                if (result !== null) {
                    drawTree(result);
                } else {
                    /* There is no material present */
                    $(treeDOMTarget).html($T('No Material Found.'));
                }
            } else {
                /* Handle error */
            }
        });
    }

    /**
     * Event handler for clicking 'selectable' elements from the jqTree.
     */
    $(treeDOMTarget).bind('tree.click', function(event) {
        $('#materialTitle').html(event.node.name);
        $('#materialDownloadChart').html(progressIndicator(true, true).dom);
        loadGraph(event.node.id, true);
    });

    loadTree();
});
