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

// Returns the (inner) size of the browser window
function getWindowDimensions() {
    var dim = {width: 0, height: 0};

    if( typeof( window.innerWidth ) == 'number' ) {
        // Non-IE
        dim.width = window.innerWidth;
        dim.height = window.innerHeight;
    } else if( document.documentElement && ( document.documentElement.clientWidth || document.documentElement.clientHeight ) ) {
        // IE 6+ in 'standards compliant mode'
        dim.width = document.documentElement.clientWidth;
        dim.height = document.documentElement.clientHeight;
    } else if( document.body && ( document.body.clientWidth || document.body.clientHeight ) ) {
        // IE 4 compatible
        dim.width = document.body.clientWidth;
        dim.height = document.body.clientHeight;
    }
    return dim;
}

// Returns the X and Y scroll offsets
function getScrollOffset() {
    var scroll = {x: 0, y: 0};

    if( typeof( window.pageYOffset ) == 'number' ) {
        // Netscape compliant
        scroll.y = window.pageYOffset;
        scroll.x = window.pageXOffset;
    } else if( document.body && ( document.body.scrollLeft || document.body.scrollTop ) ) {
        // DOM compliant
        scroll.y = document.body.scrollTop;
        scroll.x = document.body.scrollLeft;
    } else if( document.documentElement && ( document.documentElement.scrollLeft || document.documentElement.scrollTop ) ) {
        // IE6 standards compliant mode
        scroll.y = document.documentElement.scrollTop;
        scroll.x = document.documentElement.scrollLeft;
    }
    return scroll;
}

function eventTarget(event) {
    return any(event.srcElement, event.target);
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

// Function that alwats returns true
function positive() {return true;}

//Function that alwats returns false
function negative() {return true;}

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
