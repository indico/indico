/*
 * jQuery Extra Selectors - (c) Keith Clark freely distributable under the terms of the MIT license.
 *
 * twitter.com/keithclarkcouk
 * www.keithclark.co.uk
 */

(function($) {
    function getNthIndex(cur, dir) {
        var t = cur, idx = 0;
        while (cur = cur[dir] ) {
            if (t.tagName == cur.tagName) {
                idx++;
            }
        }
        return idx;
    }

    function isNthOf(elm, pattern, dir) {
        var position = getNthIndex(elm, dir), loop;
        if (pattern == "odd" || pattern == "even") {
            loop = 2;
            position -= !(pattern == "odd");
        } else {
            var nth = pattern.indexOf("n");
            if (nth > -1) {
                loop = parseInt(pattern, 10) || parseInt(pattern.substring(0, nth) + "1", 10);
                position -= (parseInt(pattern.substring(nth + 1), 10) || 0) - 1;
            } else {
                loop = position + 1;
                position -= parseInt(pattern, 10) - 1;
            }
        }
        return (loop<0 ? position<=0 : position >= 0) && position % loop == 0
    }

    var pseudos = {
        "first-of-type": function(elm) {
            return getNthIndex(elm, "previousSibling") == 0;
        },
        "last-of-type": function(elm) {
            return getNthIndex(elm, "nextSibling") == 0;
        },
        "only-of-type": function(elm) {
            return pseudos["first-of-type"](elm) && pseudos["last-of-type"](elm);
        },
        "nth-of-type": function(elm, i, match) {
            return isNthOf(elm, match[3], "previousSibling");
        },
        "nth-last-of-type": function(elm, i, match) {
            return isNthOf(elm, match[3], "nextSibling");
        }
    };
    $.extend($.expr[':'], pseudos);
}(jQuery));
