/* This file is part of Indico.
 * Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

            var killProgress = IndicoUI.Dialogs.Util.progress();

            jsonRpc(Indico.Urls.JsonRpcService, this.method, args,
                function(response,error) {
                    if(exists(error)) {
                        killProgress();
                        self._error(error);
                    } else {
                        killProgress();
                        self.close();
                        self._success(response);
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


type("ServiceDialogWithButtons", ["ExclusivePopupWithButtons", "ServiceDialog"], {},
    function(endPoint, method, args, title, closeHandler){
        this.endPoint = endPoint;
        this.method = method;
        this.args = args;
        this.ExclusivePopupWithButtons(title, closeHandler);
    }
);



/**
 * Dialog for unforeseen errors that will ask to the user if he wants
 * to send an error report.
 */
type("ErrorReportDialog", ["ServiceDialogWithButtons"],
     {
         _sendReport: function(email) {
             var self = this;
             this.error.userMail = email.get();

             if (!$.isArray(this.error.inner)) {
                 this.error.inner = this.error.inner ? [this.error.inner] : [];
             }

             // make sure the HTML sanitization filter won't ruin everything
             _(this.error.inner).each(function(line, i) {
                 self.error.inner[i] = Util.HTMLEscape(line);
             });
             indicoRequest('system.error.report',
                           this.error,
                           function(result, error){
                               if (error) {
                                   new AlertPopup($T("Error"), $T("Unable to send your error report: ") + error.message).open();
                               }
                               else {
                                   if (result) {
                                       new AlertPopup($T("Success"), $T("Your report has been sent. Thank you!")).open();
                                   } else {
                                       new AlertPopup($T("Error"), $T("Your report could not be sent to the support address.")).open();
                                   }
                                   self.close();
                               }
                           }
                          );
         },

         draw: function() {
             this.email = new WatchObject();

             // TODO: force unidirectional binding?
             $B(this.email.accessor(), indicoSource('user.data.email.get', {}));

             var content = $('<div/>').css({
                 textAlign: 'center',
                 width: '300px'
             });
             $('<p/>').text($T('An error has occurred while processing your request. We advise you to submit an error report, by clicking "Send report".')).appendTo(content);
             $('<p/>').css('color', 'red').text(this.error.message).appendTo(content);
             var emailBlock = $('<div/>').appendTo(content);
             emailBlock.append($('<label/>').text($T('Your e-mail: ')));
             var emailInput = $B(Html.input('text', {}), this.email.accessor());
             emailBlock.append(emailInput.dom);

             return this.ServiceDialogWithButtons.prototype.draw.call(this, content);
         },

         _getButtons: function() {
             var self = this;
             return [
                 [$T('Send report'), function() {
                     self._sendReport(self.email);
                 }],
                 [$T('Do not send report'), function() {
                     self.close();
                 }]
             ];
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
        return this.error.title || $T("Warning");
    },

    __getContent: function() {
        var content = Html.div({style: {textAlign: 'left'}});
        content.append(Html.div({}, this.error.message));
        content.append(Html.unescaped.div("warningExplanation", this.error.explanation));

        if (this.error.code == 'ERR-P4' || (this.error.code == 'Forbidden' && !this.error.hasUser)) {
            content.append(Html.div({style:{marginTop:pixels(10)}},
                    Html.a({href: build_url(Indico.Urls.Login, {next: document.URL})}, $T("Go to login page"))));
        }

        return content.dom;
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
                 $('<div class="loadingPopup"/>').append($('<div class="text"/>').html(this.text)),
                 {background: '#424242', border: 'none', padding: '20px', overflow: 'visible'},
                 {background: '#424242', border: 'none', padding: '1px', overflow: 'auto', display:"inline"}
             );
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
