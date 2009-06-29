type('TouchSensitive', [],
     {
         addSense : function(element) {

             var self = this;
             element.observeEvent('mouseover', function(event) {
                 if (self.enabled) {
                     if (!element.ancestorOf($E(eventTarget(event)))) {
                         return;
                     }

                     each(self.actionOnList, function(action) {
                         action();
                     });
                 }
                 event.preventDefault();
             });

             element.observeEvent('mouseout', function(event) {
                 if (self.enabled) {
                     if (element.ancestorOf($E(event.relatedTarget))) {
                         return;
                     }

                     each(self.actionOffList, function(action) {
                         action();
                     });
                 }
                 event.preventDefault();
             });

             return element;
         },

         disable : function() {
             this.enabled = false;
         },

         enable : function() {
             this.enabled = true;
         },

         addActionOn : function(action) {
             this.actionOnList.push(action);
         },

         addActionOff : function(action) {
             this.actionOffList.push(action);
         }

     },
     function() {
         this.enabled = true;
         this.actionOnList = [];
         this.actionOffList = [];
     });

type('TooltipLike', ['TouchSensitive'],
     {
         triggerOn: function() {
             if (!this.state) {
                 this._triggerOn();
                 this.state = true;
             }
         },

         triggerOff: function() {
             if (this.state) {
                 this._triggerOff();
                 this.state = false;
             }
         }

     },
     function() {
         var self = this;

         this.state = false;

         this.TouchSensitive();
         this.addActionOn(function(){
             self.triggerOn();
         });
         this.addActionOff(function(){
             self.triggerOff();
         });

     });


function highlightWithMouse(observable, target) {

    /*
     * observable - trigger element (mouse over, out)
     * target - target element (will look brighter)
     */ 

    if (target.__highlightSet) {
        return observable;
    }

    observable.observeEvent('mouseover', function(event) {
	
        target.__tmpColor = target.dom.style.backgroundColor;
        if (target.__tmpColor === ''){
            return;
        }
	
        var bgColor = target.dom.style.backgroundColor;
        var s = bgColor.match(/rgb\((\d+), (\d+), (\d+)\)/);
        if (!s) {
            s = bgColor.match(/#(..)(..)(..)/);
            s[1] = parseInt('0x'+s[1],16);
            s[2] = parseInt('0x'+s[2],16);
            s[3] = parseInt('0x'+s[3],16);
            if (!s) {
                return;
	    }
        }
	
        s[1] = Math.floor(s[1]*1.05);
        s[2] = Math.floor(s[2]*1.05);
        s[3] = Math.floor(s[3]*1.05);
        target.setStyle('backgroundColor', 'rgb(' + s[1] + ',' + s[2] + ',' + s[3] + ')');

    });
    
    observable.observeEvent('mouseout', function(event) {
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
    }
)