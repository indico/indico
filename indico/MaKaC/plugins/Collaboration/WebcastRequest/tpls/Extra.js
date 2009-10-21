var WR_hideTalks = function () {
    IndicoUI.Effect.disappear($E('contributionsDiv'));
}

var WR_loadTalks = function () {
    
    var fetchContributions = function() {
        
        var talkTemplate = function(talk) {
            var checkBox = Html.input('checkbox', {name: "talkSelection", id: "talk" + talk.id + "CB"});
            checkBox.dom.value = talk.id; 
            var talkId = Html.span("WRContributionId", "[" + talk.id + "] ")
            var talkName = Html.span("WRContributionName", talk.title)
            var label = Html.label({}, talkId, talkName);
            label.dom.htmlFor = "talk" + talk.id + "CB";
            
            if (talk.speakerList.length > 0) {
                var speakers = ", by "
                enumerate(talk.speakerList, function(speaker, index) {
                    if (index > 0) {
                        speakers += " and ";
                    }
                    speakers += speaker.fullName;
                });
                label.append(Html.span("WRSpeakers", speakers))
            }
            
            if (exists(talk.location) && trim(talk.location)) {
                var locationText = ' (' + talk.location;
                if (exists(talk.room) && trim(talk.room)) {
                    locationText += ', ' + talk.room;
                }
                locationText += ')';
                label.append(Html.span("WRSpeakers", locationText))
            }
            
            var li = Html.li();
            li.append(checkBox);
            li.append(label);
            return li;
        };
        
        var killProgress = IndicoUI.Dialogs.Util.progress($T("Fetching talks, may take a while..."));
        indicoRequest('collaboration.pluginService',
            {
                plugin: 'WebcastRequest',
                service: 'WebcastAbleTalks',
                conference: '<%= ConferenceId %>'
            },
            function(result, error){
                if (!error) {
                    if (result.length > 0) {
                        for (i in result) {
                            t = result[i];
                            if (i < result.length / 2) {
                                $E('contributionList1').append(talkTemplate(t));
                            } else {
                                $E('contributionList2').append(talkTemplate(t));
                            }
                        }
                    } else {
                        $E('contributionList1').set(Html.span({style:{paddingLeft: pixels(20)}}, $T("This event has no talks, or none of the talks take place in a room capable of webcasting.")));
                    }
                    IndicoUI.Effect.appear($E('contributionsDiv'));
                    WR_contributionsLoaded = true;
                    killProgress();
                } else {
                    killProgress();
                    IndicoUtil.errorReport(error);
                }
            }
        );
    };
    
    if (WR_contributionsLoaded) {
        IndicoUI.Effect.appear($E('contributionsDiv'));
    } else {
        fetchContributions();
    }
    
}
