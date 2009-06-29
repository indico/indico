type("PicList", ["WatchList"], {

    renderItem: function (item) {
        return item.draw();
    },

    addItem: function() {
        var addPic = new PicItem(this, 'edit');
        this.insert(addPic, '0');
    },

    deleteItem: function(item) {
        var self = this;
        var killProgress = IndicoUI.Dialogs.Util.progress();
        jsonRpc(Indico.Urls.JsonRpcService, 'event.pic.delete', {'picId': item.id, 'conference':self.confId},
                function(response, error){
                    if (exists(error)) {
                        killProgress();
                        IndicoUtil.errorReport(error);
                    }
                    else {
                        killProgress();
                        self.remove(item);
                    }
                });
    }

},

     function(picslist, web_container, uploadAction, confId) {
         this.WatchList();
         this.uploadAction = uploadAction;
         this.confId = confId
         var self = this;
         each(picslist, function(item){
             self.append(new PicItem(self, 'display', item));
         });
         $B($E(web_container), this, this.renderItem);
     }

    );


type("PicItem", ["IWidget"], {

    _iFrameLoaded : function(iframeId) {
        var doc;
        
        if (Browser.IE) {
            // *sigh*
            doc = document.frames[iframeId].document;
        } else {
            doc = $E(iframeId).dom.contentDocument;
        }
    
        var res = Json.read(doc.body.innerHTML);

        if (res.status == "ERROR") {
            IndicoUtil.errorReport(res.info);
        } else {
            this.id = res.info.id;
            this.picURL = res.info.picURL;
            this.chooser.set('display');
        }
    },

    draw: function() {
        var self = this;

        this.chooser = new Chooser(new Lookup({
            edit: function() {
                var stuffUploadForm = function(inputField, uploadType, submitText) {
                    var killProgress;
                    var frameId = Html.generateId();
                    var form = Html.form({target: frameId, method: 'post', id: Html.generateId(),
                        action: self.parentList.uploadAction,
                        enctype: 'multipart/form-data'});
                    
                    form.append(inputField);

                    form.append(Widget.button(
                        command(function(){
                            self.uploading = true;
                            killProgress = IndicoUI.Dialogs.Util.progress();
                            form.dom.submit();
                        }, submitText)
                    ));

                    var iframe = Html.iframe({id: frameId, name: frameId, style: {display: 'none'}});

                    var loadFunc = function() {
                        if (self.uploading) {
                            killProgress();
                            self.uploading = false;
                            // need to pass the ID, due to IE
                            self._iFrameLoaded(frameId);
                        }
                    };

                    if (Browser.IE) {
                        // cof! cof!
                        iframe.dom.onreadystatechange = loadFunc;
                    } else {
                        // for normal browsers
                        iframe.observeEvent("load", loadFunc);
                    }

                    return Html.div({}, [form, iframe]);
                };

                var fileUpload = stuffUploadForm(Html.input('file', {name: 'file'}), 'file', 'Upload');


                var closeArea = Html.div({},Widget.button(
                    command(function() {
                        self.parentList.remove(self);
                    },"Close")));

                return this.IWidget.prototype.draw.call(this, Html.div({},[fileUpload, closeArea]));
            },
            display: function() {
                var image = Html.img({
                    src: ""+self.picURL,
                    alt: 'Picture preview',
                    title: 'Picture preview',
                    style: {
                        width: "10%",
                        height: "10%",
                        border: "0px"
                    }
                });
                var linkToUse = Html.span({style:{color: 'green'}});
                linkToUse.set(Html.a({href:self.picURL}, self.picURL));

                var remButton = Widget.link(command(function (){
                    self.parentList.deleteItem(self);
                }, IndicoUI.Buttons.removeButton()));

                return Html.div({}, [image, linkToUse, remButton]);
            }
        }));

        this.chooser.set(this.choice);

        return Widget.block(this.chooser);

        //path = str(urlHandlers.UHConferencePic.getURL( self._conf))+"&PicId=%s"%str(i)
        //html = html + """<img src=\"%s\" border=\"0\" style=\"width:50px;height:50px;\"></img>"""%path
        //html = html + """<b>Link to use in CSS : <a href=\"%s\" target=\"blank\">%s</a></b>"""%(path,path)
        /*html = html + _("""<form action=\"%s&picId=%s\" method="POST"><input type="submit" class="btn" value="_("X")"></form>""")%(urlHandlers.UHRemovePic.getURL(self._conf),str(i))
                html = html + """<br>"""*/
    }
},

     function(parentList, choice, item) {
         this.choice = choice;
         this.parentList = parentList;
         if (item) {
             extend(this, item);
         }
         //this.ServiceWidget(Indico.Urls.JsonRpcService, 'pics.add', {});
     }
    );
