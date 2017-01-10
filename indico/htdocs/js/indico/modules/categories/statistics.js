/* This file is part of Indico.
 * Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

/* global processJqPlotOptions:false */

$(function initCategoryStats() {
    'use strict';

    $('.plot-container .plot').each(function drawPlot() {
        var $this = $(this);
        var xMin = $this.data('min-x');
        var xMax = $this.data('max-x');
        var yMin = $this.data('min-y');
        var yMax = $this.data('max-y');

        var data = $this.data('values') || {};

        var currentYear = new Date().getFullYear();
        var current = [[currentYear, data[currentYear]]];

        var options = {
            axes: {
                xaxis: {
                    label: $this.data('label-xaxis'),
                    max: xMax,
                    min: xMin,
                    tickOptions: { showGridline: false }
                },
                yaxis: {
                    label: $this.data('label-yaxis'),
                    max: yMax,
                    min: yMin
                }
            },
            height: 400,
            highlighter: {
                location: 'n',
                tooltipAxes: 'yx',
                tooltipSeparator: $this.data('tooltip')
            },
            series: [
                {
                    fillAlpha: 0.9,
                    fill: true,
                    fillAndStroke: true
                }, {
                    markerOptions: {
                        color: '#005272',
                        style: 'circle'
                    }
                }
            ],
            width: 400
        };
        data = [
            _.pairs(data).map(function(datum) {
                return [parseInt(datum[0], 10), datum[1]];
            }),
            current
        ];
        var plot = $.jqplot(this.id, data, processJqPlotOptions(options));
        $(window).resize(function() {
            plot.replot({ resetAxes: true });
        });
    });
});
