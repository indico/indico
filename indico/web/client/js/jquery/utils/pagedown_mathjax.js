// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* eslint-disable camelcase, one-var, no-lonely-if, import/unambiguous */
/* global Markdown:false, MathJax:false, PageDownMathJax:false */

(function() {
  var DELIMITERS = [['$', '$'], ['$$', '$$']];

  window.PageDownMathJax = function() {
    var $preview = null; // the preview container

    var blocks, start, end, last, braces; // used in searching for math
    var math; // stores math until markdone is done

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
        .replace(/&/g, '&amp;') // use HTML entity for &
        .replace(/</g, '&lt;') // use HTML entity for <
        .replace(/>/g, '&gt;'); // use HTML entity for >
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
    // When the preview changes, cancel MathJax and restart,
    // if we haven't done that already.
    //
    function updateMJ(elem, cb) {
      if (elem.dataset.noMathjax !== undefined) {
        cb();
      } else {
        typeset($preview.get(0)).then(cb);
      }
    }

    async function typeset(elem) {
      if (elem.dataset.noMathjax !== undefined) {
        return;
      }

      // https://docs.mathjax.org/en/latest/web/typeset.html#handling-asynchronous-typesetting
      MathJax.startup.promise = MathJax.startup.promise
        .then(() => MathJax.typesetPromise([elem]))
        .catch(err => console.log(`[MathJax] Typeset failed: ${err.message}`));
      return MathJax.startup.promise;
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
      MathJax.startup.promise.then(preview);
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
      return typeset(elem);
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

  $.fn.pagedown = function() {
    function _pagedown(elem) {
      const pd_context = PageDownMathJax();
      elem.data('pagedown', pd_context);
      pd_context.createEditor(elem.get(0));
    }

    $(this).each(function(i, elem) {
      _pagedown($(elem));
    });
  };
})();
