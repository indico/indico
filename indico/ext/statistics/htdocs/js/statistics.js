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

    /**
     * Reconstruct the query string based on local values and force relocation.
     */
    $('#updateQuery').click(function() {
        var url = 'statistics?';
        url += buildURI();
        window.location.href = url;
    });

    /**
     * Provides the 'info' tooltip handling for Visitor Hit Rates
     */
    $('#visitsInfoHelp').qtip({
        content: $('#statsInfoHidden').html(),
        position: {
            my: 'top middle',
            at: 'bottom middle'
        },
        style: {
            classes: 'qtip-rounded qtip-shadow qtip-light'
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
    var drawGraph = function(source, DOMTarget, replot) {

        // Clear the DOM target
        $('#' + DOMTarget).html('');

        var plotOptions = {
            axes: {
                xaxis: {
                    renderer:$.jqplot.DateAxisRenderer,
                    min: reportDates.start,
                    max: reportDates.end
                },
                yaxis: {
                    min: 0,
                    numberTicks: 10
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
            legend: {
                show: true,
                location: 'nw'
            },
            grid: {
                background: '#FFFFFF',
                shadow: false
            },
            series: [{
                showMarker:false,
                lineWidth: 1,
                color: '#CCCCCC',
                label: $T('Total Hits')
            }, {
                showMarker:false,
                lineWidth: 1,
                color: '#0B63A5',
                label: $T('Unique Hits')
            }]
        };

        // Create the plot here
        if (replot) {
            $.jqplot(DOMTarget, source, plotOptions).replot();
        } else {
            $.jqplot(DOMTarget, source, plotOptions);
        }

    };

    /**
     * Base values for API requests, to be extended as needed.
     */
    var getIndicoBaseParams = function() {
        var indicoBaseParams = {
            startDate: $('#statsFilterStartDate').val(),
            endDate: $('#statsFilterEndDate').val(),
            confId: $('#confId').val()
        };

        var contribId = $('#contribId').val();

        // We only want to append if it's not the internal 'None' flag.
        if (contribId != 'None') {
            indicoBaseParams['contribId'] = contribId;
        }

        return indicoBaseParams;
    };

    /**
     * Loads hit rate data via AJAX to propagate the main Visitors Graph.
     */
    var loadVisitorsGraph = function(data) {
        var DOMTarget = 'visitorChart';
        $('#' + DOMTarget).html(progressIndicator(true, true).dom);

        indicoRequest('piwik.getEventVisits', getIndicoBaseParams(),
            function(result, error) {
                if (!error) {
                    var source = [getArrayValues(result, 'total_hits'),
                                  getArrayValues(result, 'unique_hits')]

                    drawGraph(source, DOMTarget, false);
                } else {
                    $('#' + DOMTarget).html($T('No data found.'));
                }
        });
    };

    /**
     * Loads material data via AJAX to propagate Material Graph(s)
     */
    var loadMaterialGraph = function(uri, replot) {
        replot = typeof replot !== 'undefined' ? replot : false;
        var DOMTarget = 'materialDownloadChart';
        var graphParams = getIndicoBaseParams();
        graphParams['materialURL'] = uri;

        indicoRequest('piwik.getMaterialStatistics', graphParams,
            function(result, error) {
                if (!error) {
                    if (result !== null) {
                        var materialHits = [getArrayValues(result['individual'],
                                            'total_hits'),
                                            getArrayValues(result['individual'],
                                            'unique_hits')];

                        drawGraph(materialHits, DOMTarget, replot);
                        // Write to the title the total material downloads
                        $('#materialTotalDownloads').html(result['cumulative']['total_hits']);
                    }
                } else {
                    $('#dialogNoGraphData').dialog('open');
                }
            }
        );
    };

    /* jqTree Specifics */
    var treeDOMTarget = '#materialTree';

    /**
     * Handles all the specific jqTree customization required.
     */
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

    /**
     * Loads the data required for jqTree via AJAX and then delegates this
     * data to drawTree for DOM insertion.
     */
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
            }
        });
    };

    /**
     * Event handler for clicking 'selectable' elements from the jqTree.
     */
    $(treeDOMTarget).bind('tree.click', function(event) {
        $('#materialTitle').html(event.node.name);
        $('#materialDownloadChart').html(progressIndicator(true, true).dom);
        loadMaterialGraph(event.node.id, true);
    });

    /**
     * jQuery UI Dialog if no data is received via AJAX (timeout)
     */
    $('#dialogNoGraphData').dialog({
        modal: true,
        resizable: false,
        autoOpen: false,
        buttons: {
            Ok: function() {
                $(this).dialog('close');
            }
        }
    });

    /* Static graph data being retrieved by the API. */
    var staticGraphs = [{
        'apiMethod': 'piwik.getGeographyGraph',
        'el': 'graphGeography'
    }, {
        'apiMethod': 'piwik.getDevicesGraph',
        'el': 'graphDevices'
    }];

    /* Iterates through the objects relating to static graphs and calls them
     * to populate page. @todo: Move this to Backbone.js
     **/
    var loadStaticGraphs = function() {
        $.each(staticGraphs, function(index, graph) {
            indicoRequest(graph.apiMethod, getIndicoBaseParams(),
                function(result, error) {
                    if (!error) {
                        $('#' + graph.el).attr('src', result);
                    } else {
                        $('#' + graph.el).html($T('No Graph Data Received'));
                    }
                });
        });
    };

    /**
     * Initializer to begin the dynamic loading of widgets etc on pageload.
     */
    var statsInit = function() {
        loadStaticGraphs();
        loadVisitorsGraph();
        loadTree();
    };

    statsInit();
});
