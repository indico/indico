
function mouseOverSwitch(observable, overAction, outAction) {

    observable.observeEvent('mouseover', function(event) {
        overAction(event);
    });

    observable.observeEvent('mouseout', function(event) {
        outAction(event);
    });

}

function showWithMouse(observable, target) {

    var stored = target.dom.style.display;
    target.dom.style.display = 'none';

    mouseOverSwitch(observable,
                    function() {
                        target.dom.style.display = stored;
                    },
                    function() {
                        target.dom.style.display = 'none';
                    });

}

function highlightWithMouse(observable, target) {

    /*
     * observable - trigger element (mouse over, out)
     * target - target element (will look brighter)
     */

    if (target.__highlightSet) {
        return observable;
    }

    mouseOverSwitch(observable,
                    function() {
                        target.__tmpColor = target.dom.style.backgroundColor;
                        if (target.__tmpColor === ''){
                            return;
                        }

                        var bgColor = target.dom.style.backgroundColor;
                        var s = bgColor.match(/rgb\((\d+), (\d+), (\d+)\)/);
                        if (!s) {
                            s = bgColor.match(/#(..)(..)(..)/);
                            if (!s) {
                                return;
                            }
                            s[1] = parseInt('0x'+s[1],16);
                            s[2] = parseInt('0x'+s[2],16);
                            s[3] = parseInt('0x'+s[3],16);
                        }

                        s[1] = Math.floor(s[1]*1.05);
                        s[2] = Math.floor(s[2]*1.05);
                        s[3] = Math.floor(s[3]*1.05);
                        target.setStyle('backgroundColor', 'rgb(' + s[1] + ',' + s[2] + ',' + s[3] + ')');
                    },
                    function() {
                        target.setStyle('backgroundColor', target.__tmpColor);
                    });

    target.__highlightSet = true;

    return observable;
}

type('Printable', [], {
    print: function(element, title) {
        var body = $E(document.body);
        var bodyCSSClasses = body.dom.className;
        var elementCSSClasses = element.dom.className;

        // Make sure element is visible when printing
        element.dom.className = elementCSSClasses + " print";

        // Make sure body is invisible
        body.dom.className = bodyCSSClasses += " noprint";

        window.print();

        // Restore
        //body.dom.className = bodyCSSClasses;
        //element.dom.className = elementCSSClasses
    }
});