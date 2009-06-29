type("ApplyForParticipationPopup", ["ExclusivePopup", "PreLoadHandler"], {
    _preload: [
        function(hook) {
            var self = this;
            indicoRequest("event.getParticipationForm", {"conference": self.confId},
                function(result, error){
                    if (error) {
                        IndicoUtil.errorReport(error);
                    }
                    else {
                        self.formHtml = result;
                        hook.set(true);
                    }
                }
            );
        }
    ],

    draw: function() {
        var div = Html.div({});
        div.dom.innerHTML = this.formHtml;
        div.dom.style.minWidth = '350px';
        div.dom.style.maxWidth = '500px';
        return this.ExclusivePopup.prototype.draw.call(this, div);
    },
    
    postDraw: function() {
        var self = this;

        this.ExclusivePopup.prototype.postDraw.call(this);
        $E('cancelRegistrationButton').observeClick(function() {self.close()});
    }
    },
    
    function(confId) {
        this.confId = confId;
        var self = this;
        this.PreLoadHandler(
                self._preload,
                function() {
                    self.open();
                });
        this.execute();
        
        this.ExclusivePopup("Apply for participation", function() {return true;})

    }
);
