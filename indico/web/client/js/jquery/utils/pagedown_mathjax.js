// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* eslint-disable camelcase, one-var, no-lonely-if */
/* global Markdown:false, MathJax:false, PageDownMathJax:false */

// General MathJax configuration
(function() {
  MathJax.Ajax.config.root =
    ($('html').data('static-site') ? 'static/' : Indico.Urls.Base) + '/dist/js/mathjax';
})();

(function() {
  var DELIMITERS = [['$', '$'], ['$$', '$$']];

  window.PageDownMathJax = function() {
    var ready = false; // true after initial typeset is complete
    var pending = false; // true when MathJax has been requested
    var $preview = null; // the preview container
    var ready_listeners = []; // the inline math delimiter

    var blocks, start, end, last, braces; // used in searching for math
    var math; // stores math until markdone is done
    var HUB = MathJax.Hub;

    //
    // Runs after initial typeset
    //
    HUB.Queue(function() {
      ready = true;
      HUB.processUpdateTime = 50; // reduce update time so that we can cancel easier
      HUB.Config({
        'HTML-CSS': {
          EqnChunk: 10,
          EqnChunkFactor: 1,
        }, // reduce chunk for more frequent updates
        'SVG': {
          EqnChunk: 10,
          EqnChunkFactor: 1,
        },
      });

      ready_listeners.forEach(listener => {
        listener();
      });
    });

    //
    // The pattern for math delimiters and special symbols
    // needed for searching for math in the page.
    //
    var SPLIT = /(\$\$?|\\(?:begin|end)\{[a-z]*\*?\}|\\[\\{}$]|[{}]|(?:\n\s*)+|@@\d+@@)/i;

    /*
     *  The math is in blocks i through j, so
     * collect it into one block and clear the others.
     * Replace &, <, and > by named entities.
     * For IE, put <br> at the ends of comments since IE removes \n.
     * Clear the current math positions and store the index of the
     * math, then push the math string onto the storage array.
     */
    function processMath(i, j) {
      var block = blocks
        .slice(i, j + 1)
        .join('')
        .replace(/&/g, '&') // use HTML entity for &
        .replace(/</g, '<') // use HTML entity for <
        .replace(/>/g, '>'); // use HTML entity for >
      if (HUB.Browser.isMSIE) {
        block = block.replace(/(%[^\n]*)\n/g, '$1<br/>\n');
      }
      while (j > i) {
        blocks[j] = '';
        j--;
      }
      blocks[i] = '@@' + math.length + '@@';
      math.push(block);
      start = end = last = null;
    }

    //
    // Break up the text into its component parts and search
    // through them for math delimiters, braces, linebreaks, etc.
    // Math delimiters must match and braces must balance.
    // Don't allow math to pass through a double linebreak
    // (which will be a paragraph).
    //
    function removeMath(text) {
      start = end = last = null; // for tracking math delimiters
      math = []; // stores math strings for latter

      blocks = text.replace(/\r\n?/g, '\n').split(SPLIT);
      for (var i = 1, m = blocks.length; i < m; i += 2) {
        var block = blocks[i];
        if (block.charAt(0) === '@') {
          //
          // Things that look like our math markers will get
          // stored and then retrieved along with the math.
          //
          blocks[i] = '@@' + math.length + '@@';
          math.push(block);
        } else if (start) {
          //
          // If we are in math, look for the end delimiter,
          // but don't go past double line breaks, and
          // and balance braces within the math.
          //
          if (block === end) {
            if (braces) {
              last = i;
            } else {
              processMath(start, i);
            }
          } else if (block.match(/\n.*\n/)) {
            if (last) {
              i = last;
              processMath(start, i);
            }
            start = end = last = null;
            braces = 0;
          } else if (block === '{') {
            braces++;
          } else if (block === '}' && braces) {
            braces--;
          }
        } else {
          //
          // Look for math start delimiters and when
          // found, set up the end delimiter.
          //
          if (block === DELIMITERS[0][0] || block === DELIMITERS[1][0]) {
            start = i;
            end = block;
            braces = 0;
          } else if (block.substr(1, 5) === 'begin') {
            start = i;
            end = '\\end' + block.substr(6);
            braces = 0;
          }
        }
      }
      if (last) {
        processMath(start, last);
      }
      return blocks.join('');
    }

    //
    // Put back the math strings that were saved,
    // and clear the math array (no need to keep it around).
    //
    function replaceMath(text) {
      text = text.replace(/@@(\d+)@@/g, function(match, n) {
        return math[n];
      });
      math = null;
      return text;
    }

    //
    // This is run to restart MathJax after it has finished
    // the previous run (that may have been canceled)
    //
    function restartMJ(cb) {
      pending = false;
      HUB.cancelTypeset = false; // won't need to do this in the future

      if ($preview) {
        typeset($preview.get(0));
      }

      if (cb) {
        HUB.Queue(cb);
      }
    }

    //
    // When the preview changes, cancel MathJax and restart,
    // if we haven't done that already.
    //
    function updateMJ(elem, cb) {
      var mathjaxEnabled = $(elem).data('no-mathjax') === undefined;
      if (!mathjaxEnabled) {
        cb();
      } else if (!pending && ready) {
        pending = true;
        HUB.cancelTypeset = false;
        HUB.Queue(restartMJ, cb);
      }
    }

    function typeset(elem) {
      if ($(elem).data('no-mathjax') === undefined) {
        HUB.Queue(['Typeset', HUB, elem]);
      }
    }

    function createPreview(elem, editorObject) {
      var converterObject = editorObject.getConverter();
      converterObject.hooks.chain('preConversion', removeMath);
      converterObject.hooks.chain('postConversion', replaceMath);

      function preview() {
        updateMJ(elem, function() {
          var new_height = $preview.outerHeight(),
            $wrapper = $preview.closest('.md-preview-wrapper'),
            is_empty = $preview.is(':empty');

          $wrapper.toggleClass('empty', is_empty);
          if (is_empty) {
            $wrapper.css('height', '');
          } else {
            $wrapper.css('height', new_height);
          }

          $preview.scrollTop(new_height);
        });
      }

      editorObject.hooks.chain('onPreviewRefresh', preview);
      typeset($preview.get(0));
      addListener(preview);
    }

    function createEditor(elem) {
      var $container = $(elem).closest('[data-field-id]');
      $preview = $container.find('.wmd-preview');

      var fieldId = $container.data('fieldId'),
        converter = Markdown.getSanitizingConverter();

      converter.hooks.chain('preBlockGamut', function block_handler(text, rbg) {
        return text.replace(/^ {0,3}""" *\n((?:.*?\n)+?) {0,3}""" *$/gm, function(whole, inner) {
          return '<blockquote>' + rbg(inner) + '</blockquote>\n';
        });
      });

      var editor = new Markdown.Editor(converter, '-f_' + fieldId, {
        helpButton: {
          handler: function() {
            return false;
          },
        },
        strings: {
          imagedialog:
            '<p><b>Insert Image</b></p><p>http://example.com/images/diagram.jpg "optional title"',
        },
      });

      createPreview(elem, editor);
      editor.run();
    }

    function mathJax(elem) {
      typeset(elem);
    }

    function addListener(listener) {
      ready_listeners.push(listener);
    }

    return {
      mathJax: mathJax,
      createEditor: createEditor,
    };
  };

  var pd = PageDownMathJax();

  window.mathJax = pd.mathJax.bind(pd);

  $.fn.mathJax = function() {
    $(this).each(function() {
      pd.mathJax(this);
    });
    return this;
  };

  $.fn.pagedown = function(arg1, arg2) {
    function _pagedown(elem) {
      var options = {},
        pd_context = elem.data('pagedown'),
        last_change = null,
        $save_button = elem.siblings('.wmd-button-bar').find('.save-button');

      function _set_saving() {
        $save_button
          .prop('disabled', true)
          .addClass('saved')
          .removeClass('saving waiting-save')
          .text($T('Saving...'));
        // the 'save' function will trigger a callback that sets
        // the final state
        options.save(elem.val(), function() {
          $save_button
            .text($T('Saved'))
            .addClass('saved')
            .removeClass('saving waiting-save');
        });
      }

      function _save_cycle(my_time) {
        return function() {
          // if there's been a change meanwhile, don't do anything
          if (last_change <= my_time) {
            // otherwise, start saving
            _set_saving();
          }
        };
      }

      if (pd_context) {
        if (arg1 === 'auto-save' && $save_button.length) {
          /*
           * This is the 'auto-save' feature
           * options:
           *   - 'wait_time' - time to wait after a change, before saving
           *   - save - function to be called on save (passed current data and callback)
           *
           * This feature also requires a '.save-button' button element to exist
           * inside '.wmd-button-bar'
           */

          _.extend(options, arg2 || {});
          elem.on('input', function() {
            $save_button
              .addClass('waiting-save')
              .removeClass('saving saved')
              .text($T('Save'))
              .prop('disabled', false);

            // let handlers (_save_cyle) know that they're out-of-date
            // by updating last_change with the current time
            last_change = new Date().getTime();
            setTimeout(_save_cycle(last_change), options.wait_time || 2000);
          });

          $save_button.on('click', function() {
            // let's kill handlers that may have been triggered
            // by setting last_change to now
            last_change = new Date().getTime();
            _set_saving();
          });
        }
      } else {
        pd_context = PageDownMathJax();
        elem.data('pagedown', pd_context);
        pd_context.createEditor(elem.get(0));
      }
    }

    $(this).each(function(i, elem) {
      _pagedown($(elem));
    });
  };
})();
