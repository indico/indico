var RR_contributionsLoaded = false;

var RR_hideTalks = function (){
    IndicoUI.Effect.disappear($E('contributionsDiv'));
}

var RR_loadTalks = function () {
    
    var fetchContributions = function() {
        
        var contributionTemplate = function(contribution) {
            var checkBox = Html.checkbox({name: "talkSelection", id: "contribution" + contribution.id + "CB"});
            checkBox.dom.value = contribution.id; 
            var contributionId = Html.span("RRContributionId", "[" + contribution.id + "]")
            var contributionName = Html.span("RRContributionName", contribution.title)
            var label = Html.label({}, contributionId, contributionName);
            label.dom.htmlFor = "contribution" + contribution.id + "CB";
            
            if (contribution.speakerList.length > 0) {
                var speakers = ", by "
                enumerate(contribution.speakerList, function(speaker, index) {
                    if (index > 0) {
                        speakers += " and ";
                    }
                    speakers += speaker.fullName;
                });
                label.append(Html.span("RRSpeakers", speakers))
            }
            
            return Html.li('', checkBox, label);
        };
        
        var killProgress = IndicoUI.Dialogs.Util.progress("Fetching contributions...");
        indicoRequest('event.contributions.list',
            {
                conference: '<%= ConferenceId %>',
                poster: false,
                posterShowNoValue: false
            },
            function(result, error){
                if (!error) {
                    if (result.length>0) {
                        for (i in result) {
                            c = result[i];
                            if (i <= result.length / 2) {
                                $E('contributionList1').append(contributionTemplate(c));
                            } else {
                                $E('contributionList2').append(contributionTemplate(c));
                            }
                        }
                    } else {
                        $E('contributionList1').set(Html.span({style:{paddingLeft: pixels(20)}},"This event has no talks")); // make this more beautiful
                    }
                    IndicoUI.Effect.appear($E('contributionsDiv'));
                    RR_contributionsLoaded = true;
                    killProgress();
                } else {
                    killProgress();
                    IndicoUtil.errorReport(error);
                }
            }
        );
    };
    
    if (RR_contributionsLoaded) {
        IndicoUI.Effect.appear($E('contributionsDiv'));
    } else {
      
        if (<%= ShouldWarn %>) {
            var title = "Loading talks";
            var popup = new ExclusivePopup (title, function(){return true});
            popup.draw = function() {
                var self = this;
                var span1 = Html.span("", "This will load a list of <%= NumberOfContributions %> talks.");
                var span2 = Html.span("", "Are you sure?");

                // We construct the "ok" button and what happens when it's pressed
                var okButton = Html.button(null, "Ok");
                okButton.observeClick(function() {
                    fetchContributions();
                    self.close();
                });

                // We construct the "cancel" button and what happens when it's pressed (which is: just close the dialog)
                var cancelButton = Html.button({style:{marginLeft:pixels(5)}}, "Cancel");
                cancelButton.observeClick(function(){
                    self.close();
                });

                var buttonDiv = Html.div({style:{textAlign:"center", marginTop:pixels(10)}}, okButton, cancelButton)

                return this.ExclusivePopup.prototype.draw.call(this, Widget.block([span1, Html.br(), span2, Html.br(), buttonDiv]));
            };
            popup.open();
        } else {
            fetchContributions();
        }

    }
}