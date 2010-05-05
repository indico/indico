
MoveTest = TestCase("MoveTest");

MoveTest.prototype.setUp = function() {

    //creating an empty historybroker
    this.historyBroker = new BrowserHistoryBroker();

    this.result = {
        day : "20091217",
        entry : {
            endDate : {
                date : "2009-12-15",
                time : "08:20:00"
            },
            entryType : "Break",
            startDate : {
                date : "2009-12-15",
                time : "08:00:00"
            }
        },
        id: "2"
    };

    this.data = {
        "20091215" : {
            "2" : {
                "startDate" : {
                    "date" : "2009-12-15",
                    "time" : "08:00:00"
                },
                "endDate" : {
                    "date" : "2009-12-15",
                    "time" : "08:20:00"
                }
            },
            "4" : {
                "startDate" : {
                    "date" : "2009-12-15",
                    "time" : "08:00:00"
                },
                "endDate" : {
                    "date" : "2009-12-15",
                    "time" : "08:20:00"
                }
            }
        },
        "20091217" : {},
        "20091216" : {
            "s0l0" : {
                "startDate" : {
                    "date" : "2009-12-16",
                    "time" : "08:00:00"
                },
                "sessionSlotId" : "0",
                "endDate" : {
                    "date" : "2009-12-16",
                    "time" : "09:00:00"
                },
            }
        }
    };

    this.eventInfo = {
        "startDate" : {
            "date" : "2009-12-15",
            "time" : "08:00:00"
        },
        "endDate" : {
            "date" : "2009-12-17",
            "time" : "18:00:00"
        }
    };

    //Mock, since we do not need any GUI, we fake this object
    function WrappingElement(){
        this.setStyle = function(x, y){
            return true;
        };
    }
    this.wrappingElement = new WrappingElement();

};


MoveTest.prototype.testUpdateEntry = function() {
    //function(data, eventInfo, width, wrappingElement, detailLevel, historyBroker, isSessionTimetable)
    var tlmt = new TopLevelManagementTimeTable(this.data, this.eventInfo, "5", this.wrappingElement, null, this.historyBroker, false);
    tlmt.currentDay = "20091215";

    //_updateMovedEntry: function(result, oldEntryId)
    tlmt._updateMovedEntry(this.result, "2");

    var expectedData = "{\"4\":{\"startDate\":{\"date\":\"2009-12-15\",\"time\":\"08:00:00\"},\"endDate\":{\"date\":\"2009-12-15\",\"time\":\"08:20:00\"}}}";

    //checking of the Break has been moved
    assertEquals("Old entry should have been removed", expectedData, Json.write(tlmt.data['20091215']));
    assertEquals("New entry location", "Break", tlmt.data['20091217']['2']['entryType']);

};

