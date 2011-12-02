type("RegistrationUploadFile",[],
        {
        draw: function ()
        {
            return this.uploadWidget;
        }

        },
        function(id, valueDisplay, fileName, mandatory){

            var imageRemove = Html.img({
                src: imageSrc("remove"),
                alt: $T('Remove attachment'),
                title: $T('Remove this attachment'),
                id: 'remove'+id,
                style:{marginLeft:'15px', cursor:'pointer', verticalAlign:'bottom'}
            });

            var uploadFileInput = Html.input('file', {id: id, name: id});
            var existingAttachment = Html.div({id:'existingAttachment'+id}, $(valueDisplay)[0],
                                                  imageRemove,
                                                  Html.input("hidden",{id: id, name: id}, fileName));

            $(imageRemove.dom).click(function(e) {
                $E("attachment"+id).set(uploadFileInput);
                if(mandatory){
                    addParam($E(id), 'text', false);
                }
            });

            if(valueDisplay){
                this.uploadWidget = existingAttachment
            } else{
                this.uploadWidget = uploadFileInput;
            }

        });