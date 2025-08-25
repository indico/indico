// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

// jqplot isn't a real JS module. We have to explicitly load the files we need

import './compat/jqplot';

import _ from 'lodash';

(function setupStatistics(global) {
  global.processJqPlotOptions = function processJqPlotOptions(options) {
    const jqPlotDefaultOptions = {
      animate: !$.jqplot.use_excanvas,
      animateReplot: !$.jqplot.use_excanvas,
      axesDefaults: {
        labelRenderer: $.jqplot.CanvasAxisLabelRenderer,
        tickRenderer: $.jqplot.CanvasAxisTickRenderer,
        tickOptions: {
          markSize: 0,
          formatString: '%d',
        },
      },
      cursor: {
        show: true,
        showTooltip: false,
        zoom: false,
      },
      grid: {
        background: 'transparent',
        drawBorder: false,
        shadow: false,
      },
      highlighter: {show: true},
      legend: {show: false},
      seriesColors: ['#007CAC'], // indico blue
      seriesDefaults: {
        markerOptions: {
          style: 'filledCircle',
          color: '#007CAC', // indico blue
        },
        lineWidth: 3,
        pointLabels: {
          show: false,
          color: 'white',
          location: 'w',
          xpadding: 4,
          edgeTolerance: -2,
        },
        rendererOptions: {
          animation: {speed: 1000},
          highlightColors: '#0085B9',
          smooth: true,
        },
        shadow: false,
        size: 11,
      },
    };
    return $.extend(true, {}, jqPlotDefaultOptions, options);
  };

  $(document).ready(() => {
    $('.i-progress > .i-progress-bar').width(function getProgress() {
      return $(this).data('progress');
    });
    // Animate numerical values in badges
    $('.i-badge .i-badge-value[data-value]').each(function loadValue() {
      const $this = $(this);
      const val = $this.data('value');
      if (!_.isNumber(val) || val === 0) {
        $this.text(val);
        return;
      }
      $({Counter: 0}).animate(
        {Counter: val},
        {
          duration: 1000,
          easing: 'swing',
          step() {
            $this.text(Math.ceil(this.Counter));
          },
        }
      );
    });
  });
})(window);
