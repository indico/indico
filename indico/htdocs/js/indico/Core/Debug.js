type("DebugWindow", [],
     {
         buildDialog : function() {

             this.debugInfo = Html.textarea({style:
                                             {width: '100%',
                                              height: '100%',
                                              background: 'red'}},
                                            '');

             return Html.div({style: {border: '1px dashed black',
                                      opacity: 0.7,
                                      position: 'fixed',
                                      width: '100%',
                                      bottom: '0px',
                                      height: '100px',
                                      left: '0px'
                                     }}, this.debugInfo);
         },
         addText: function(text) {
             this.debugInfo.set(this.debugInfo.get() + text + '\n');
         }
     },
     function() {
         $E(document.body).append(this.buildDialog());
     }
    );

debugWindow = null;

function createDebugWindow() {
    debugWindow = new DebugWindow();
}

function debug(text){
    if (debugWindow) {
        debugWindow.addText(text);
    }
}

type("DebugObjectBox", [],
     {
         buildDialog : function(obj) {

             var list = $B(Html.ul({}), obj,
                 function(item) {
                     return Html.li({}, item.key + ': ', $B(Html.input('text'), item));
                 });


             return $B(Html.div({style: {border: '1px dashed black',
                                         opacity: 0.7,
                                         position: 'fixed',
                                         width: '300px',
                                         top: pixels(this.y),
                                         height: '100px',
                                         left: pixels(this.x),
                                         background: 'green'
                                        }}), list);
         }

     },
     function(obj, x, y) {
         this.x = x;
         this.y = y;

         $E(document.body).append(this.buildDialog(obj));
     }
    );

function debugObjectBox(obj, x, y) {
    new DebugObjectBox(obj, x, y);
}