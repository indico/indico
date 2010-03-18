type("PreLoadHandler", [],
     {
         execute: function() {

             var self = this;

             if (this.counter === 0) {
                 this.process();
             } else {
                 $L(this.actionList).each(function(preloadItem) {

                     var hook = new WatchValue();
                     hook.set(false);
                     hook.observe(function(value){
                         if (value) {
                             bind.detach(hook);
                             self.counter--;

                             if (self.counter === 0) {
                                 self.process();
                             }
                         }
                     });

                     if (preloadItem.PreLoadAction) {
                         preloadItem.run(hook);
                     } else {
                         preloadItem.call(self, hook);
                     }
                 });
             }
         }
     },
     function(list, process) {
         this.actionList = list;
         this.counter = list.length;
         this.process = process;
     }
    );


type("ServiceDialog", ["ExclusivePopup"],
     {
         _error: function(error) {
             IndicoUI.Dialogs.Util.error(error);
         },

         request: function(extraArgs) {
             var self = this;
             var args = extend(clone(this.args), extraArgs);

             var progressDialog = new ProgressDialog();
             progressDialog.open();

             jsonRpc(Indico.Urls.JsonRpcService, this.method, args,
                     function(response,error) {
                         if(exists(error)) {
                             progressDialog.close();
                             self._error(error);
                         } else {
                             self._success(response);
                             progressDialog.close();
                             self.close();
                         }
                     }
                    );
         }
     },

     function(endPoint, method, args, title, closeHandler) {
         this.endPoint = endPoint;
         this.method = method;
         this.args = args;
         this.ExclusivePopup(title, closeHandler);
     }
    );



/**
 * Dialog for unforeseen errors that will ask to the user if he wants
 * to send an error report.
 */
type("ErrorReportDialog", ["ServiceDialog"],
     {
         _sendReport: function(email) {
             var self = this;
             this.error.userMail = email.get();
             indicoRequest('system.error.report',
                           this.error,
                           function(result, error){
                               if (error) {
                                   alert($T("Unable to send your error report: ") + error.message);
                               }
                               else {
                                   if (result) {
                                       alert($T("Your report has been sent. Thank you!"));
                                   } else {
                                       alert($T("Your report could not be sent to the support address."));
                                   }
                                   self.close();
                               }
                           }
                          );
         },

         draw: function() {
             var self = this;
             var email = new WatchObject();

             // TODO: force unidirectional binding?
             $B(email.accessor(), indicoSource('user.data.email.get', {}));

             return this.ServiceDialog.prototype.draw.call(
                 this,
                 Html.div(
                     {style:{padding:pixels(10)}},
                     Html.div({style:{marginBottom: pixels(10), width:'300px', textAlign: 'center'}}, $T('An error has occurred while processing your request. We advise you to submit an error report, by clicking "Send report".')),
                     Html.div({style:{color: 'red', marginBottom: pixels(10), width: '300px', height: '75px', textAlign: 'center', overflow: 'auto'}},
                              this.error.code+": "+this.error.message),
                     Html.div({style:{marginBottom: pixels(10), textAlign: 'center'}},
                              Html.label({},"Your e-mail: "),
                              $B(Html.input("text",{}), email.accessor())),
                     Html.div({style:{textAlign: 'center'}},
                              Widget.link(command(
                                  function() {
                                      self._sendReport(email);
                                  },
                                  Html.input('button', {},'Send report'))),
                              Widget.link(command(
                                  function() {
                                      self.close();
                                  },
                                  Html.input('button', {style:{marginLeft: pixels(5)}},'Do not send report')
                              ))
                             )
                 ));
         }
     },
     function(error) {
         this.error = error;
     }
);

/**
 * Dialog for errors whose type is "noReport", such as "not logged in" warning
 */
type("NoReportErrorDialog", ["AlertPopup"], {

    __getTitle: function() {
        return Html.span('warningTitle', $T("Warning"));
    },

    __getContent: function() {

        var content = Html.div({style: {textAlign: 'center'}});
        content.append(Html.span({}, this.error.message));

        if (this.error.code == 'ERR-P4') {
            content.append(Html.div({style:{marginTop:pixels(10)}},
                    Html.a({href: Indico.Urls.Login+'?returnURL='+document.URL}, $T("Go to login page"))));
        }

        return content;
    }
},
    function(error){
        this.error = error;
        this.AlertPopup(this.__getTitle(), this.__getContent());
    }
);

type("ProgressDialog",["ExclusivePopup"],
     {
         draw: function() {
             return this.ExclusivePopup.prototype.draw.call(
                 this,
                 Html.div('loadingPopup',
                          Html.div('text', this.text)),
                 {background: '#424242', border: 'none', padding: '20px'});
         }
     },
     function(text) {
         if (text === undefined) {
             this.text = $T('Loading...');
         } else {
             this.text = text;
         }
         this.ExclusivePopup();
     }
    );

IndicoUI.Dialogs = {};
