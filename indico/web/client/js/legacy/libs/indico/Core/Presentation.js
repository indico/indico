/* This file is part of Indico.
 * Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

// Extensions to Presentation
// Candidates for integration?

extend(Html.prototype,
       {
           ancestorOf: function(child) {
               if (!child) {
                   return false;
               } else if (this.dom == child.dom) {
                   return true;
               } else if (child.getParent() === null){
                   return false;
               } else if (child.getParent() == this){
                   return true;
               } else if (child.getParent().dom == document.body) {
                   return false;
               } else {
                   return this.ancestorOf(child.getParent());
               }
           },
           replaceWith: function(element) {
               this.getParent().dom.replaceChild(element.dom, this.dom);
           }
       });

extend(WatchObject.prototype,
       {
           clone: function() {
               return $O(this.getAll());
           }
       }
      );

function eventTarget(event) {
    return any(event.srcElement, event.target);
}

function $N(name) {
    return translate(document.getElementsByName(name), $E);
}

// Function that always returns true
function positive() {return true;}


function createObject(clazz, args) {
    function Dummy(){}

    Dummy.prototype = clazz.prototype;
    var x = new Dummy();
    x.constructor = clazz;
    clazz.apply(x, args);

    return x;
}

function escapeHTML(html) {
    // from Prototype
    return html.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

var SortCriteria = {
    Default: function(e1, e2) {
        return e1 == e2?0:(e1 < e2?-1:1);
    },
    Integer: function(e1, e2) {
        if (isNaN(parseInt(e1,10)) ||
            isNaN(parseInt(e2,10))) {
            return SortCriteria.Default(e1, e2);
        } else {
            return parseInt(e1,10) == parseInt(e2,10)?0:(parseInt(e1,10) < parseInt(e2,10)?-1:1);
        }
    }
};

function partition(list, start, end, index, cmp) {
    var pval = list.item(index);
    list.swap(index, end);
    var store = start;

    for (var i=start;i < end;++i) {
        if (cmp(list.item(i), pval) < 0) {
            list.swap(i, store);
            store++;
        }
    }

    list.swap(store, end);
    return store;
}

function quicksort(list, start, end, cmp) {
    if (end > start) {
        var pnew = partition(list, start, end, start, cmp);
        quicksort(list, start, pnew - 1, cmp);
        quicksort(list, pnew + 1, end, cmp);
    }

}

extend(WatchList.prototype,
       {
           swap: function(source, destination) {
               var itemS = this.item(source);
               var itemD = this.item(destination);
               this.replaceAt(source, itemD);
               this.replaceAt(destination, itemS);
           },

           sort: function(compare) {
               compare = compare || SortCriteria.Default;
               quicksort(this, 0, this.length.get()-1, compare);
           }

       });

Html.unescaped = map({'div': null, 'span': null}, function(value, elemType) {
    return function() {
        var res = Html[elemType].apply(this, arguments);
        res.dom.innerHTML = res.get();
        return res;
    };
});

declareMixin = function(targetName, sourceName, mixins) {
    type(targetName, [sourceName].concat(mixins), {},
     function() {
         this[sourceName].apply(this, arguments);
     });
};
