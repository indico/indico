/* This file is part of Indico.
 * Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
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
           getElementsByClassName: function(name){
               if(document.getElementsByClassName) {
                   return translate(this.dom.getElementsByClassName(name),
                             $E);
               } else {
                   // check for XPath
                   if (!!document.evaluate) {
                       /* from Prototype */

                       var expression = ".//*[contains(concat(' ', @class, ' '), ' " + name + " ')]";
                       var results = [];
                       var query = document.evaluate(expression, this.dom, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                       for (var i = 0, length = query.snapshotLength; i < length; i++) {
                           results.push(query.snapshotItem(i));
                       }
                       return translate(results,
                                        $E);
                   } else {
                       var children = this.dom.getElementsByTagName('*');
                       var elements = [], child;
                       for (var j = 0, length2 = children.length; j < length2; j++) {
                           child = children[j];
                           if (child.className == name) {
                               elements.push(child);
                           }
                       }
                       return translate(elements, $E);
                   }
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

// Returns the x and y coordinates for the mouse pointer
function getMousePointerCoordinates(e) {
    e = e || window.event;

    var cursor = {x:0, y:0};

    if (e.pageX || e.pageY) {
        cursor.x = e.pageX;
        cursor.y = e.pageY;
    }
    else {
        var de = document.documentElement;
        var b = document.body;
        cursor.x = e.clientX +
            (de.scrollLeft || b.scrollLeft) - (de.clientLeft || 0);
        cursor.y = e.clientY +
            (de.scrollTop || b.scrollTop) - (de.clientTop || 0);
    }
    return cursor;
}

function eventTarget(event) {
    return any(event.srcElement, event.target);
}

function relatedTarget(event) {
    return any(event.relatedTarget, event.toElement);
}

function stopPropagation(event) {
    if (event.stopProgagation) {
        event.stopPropagation();
    } else {
        event.cancelBubble = true;
    }
}

function $N(name) {
    return translate(document.getElementsByName(name), $E);
}

function flatten(array) {
    // replace by linearize() when it's working properly?

    if (!isArray(array)) {
        return [array];
    } else if (array.length === 0) {
        return [];
    }

    var elem = array.splice(0,1);
    return concat(flatten(elem[0]), flatten(array));

}

// Function that always returns true
function positive() {return true;}

//Function that always returns false
function negative() {return false;}

//Function to sort arrays of integers
var numberSorter = function(a, b) {
    return a - b;
};

// Utility function to get the selected items in a select box with multiple selection
var getSelectedItems = function(select) {
    var selectedItems = [];
    for (var i=0; i<select.dom.length; i++) {
        if (select.dom.options[i].selected) {
            selectedItems.push(select.dom[i].value);
        }
    }
    return(selectedItems);
};

function createObject(clazz, args) {
    function Dummy(){}

    Dummy.prototype = clazz.prototype;
    var x = new Dummy();
    x.constructor = clazz;
    clazz.apply(x, args);

    return x;
}

function filter(array, func)
{
    var len = array.length;

    var res = [];
    for (var i = 0; i < len; i++)
    {
        if (i in array)
        {
            var val = array[i];
            if (func(val))
            {
                res.push(val);
            }
        }
    }
    return res;
}

function escapeHTML(html) {
    // from Prototype
    return html.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function invertableBind(target, source, invert, template) {
    var invTemplate = template?{
        toSource: template.toTarget,
        toTarget: template.toSource
    }:null;
    return invert?$B(source, target, invTemplate):
        $B(target, source, template);
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
    },
    DashSeparated: function(e1, e2) {
        // sorting format: int-string-string-...
        // for example 41-R2-020
        var e1Array = e1.split('-');
        var e2Array = e2.split('-');
        for (var i = 0; i < e1Array.length; i++) {
          if (i == 0) {
              var result = SortCriteria.Integer(e1Array[i], e2Array[i]);
          }
          else {
              var result = SortCriteria.Default(e1Array[i], e2Array[i]);
          }
          if (result != 0)
              return result;
        };
        return 0;
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

type("WatchOrderedDict", ["WatchObject"],
     {

         // ATTENTION: Implementation not complete!
         // remove() functions missing!

         sort: function(compare) {
             this.order.sort(compare);
         }
     },
     function() {
         this.order = $L();
         this.WatchObject();

         var self = this;

         this.each = function(iterator) {
             self.order.each(function(val, i) {
                 return iterator(self.get(val), val);
             });
             return iterator.result;
         };

         this.set = function(key, value) {
             this.order.add(key);
             this.WatchObject.prototype.set.call(key, value);
         };

         var oldUpdate = this.update;
         var oldClear = this.clear;

         this.update = function(values) {

             var self = this;

             each(values, function(value, key) {
                 self.order.append(key);
             });

             oldUpdate.call(this, values);
         };

         this.clear = function() {
             this.order.clear();
             return oldClear();
         };

     });

function $D(source, template) {
        return bind.toDictionary(new WatchOrderedDict(), source, template);
}

String.prototype.replaceAll = Browser.Gecko?
    function(pattern, replace) {
        return this.replace(pattern, replace, 'g');
    }:
    function(pattern, replace) {
        return this.replace( new RegExp( pattern, "g" ), replace );
    };


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
