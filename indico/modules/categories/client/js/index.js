// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import './display';

(function(global) {
  global.setupCategoryStats = function setupCategoryStats() {
    $(document).ready(() => {
      $('.plot-container .plot').each((__, element) => {
        const $this = $(element);
        const xMin = $this.data('min-x');
        const xMax = $this.data('max-x');
        const yMin = $this.data('min-y');
        const yMax = $this.data('max-y');

        var data = $this.data('values') || {};

        const currentYear = new Date().getFullYear();
        const current = [[currentYear, data[currentYear]]];

        const options = {
          axes: {
            xaxis: {
              label: $this.data('label-xaxis'),
              max: xMax,
              min: xMin,
              tickOptions: {showGridline: false},
            },
            yaxis: {
              label: $this.data('label-yaxis'),
              max: yMax,
              min: yMin,
            },
          },
          height: 400,
          highlighter: {
            location: 'n',
            tooltipAxes: 'yx',
            tooltipSeparator: $this.data('tooltip'),
          },
          series: [
            {
              fillAlpha: 0.9,
              fill: true,
              fillAndStroke: true,
            },
            {
              markerOptions: {
                color: '#005272',
                style: 'circle',
              },
            },
          ],
          width: 400,
        };
        data = [_.pairs(data).map(datum => [parseInt(datum[0], 10), datum[1]]), current];
        const plot = global.$.jqplot(element.id, data, global.processJqPlotOptions(options));
        $(window).resize(() => {
          plot.replot({resetAxes: true});
        });
      });
    });
  };
})(window);
