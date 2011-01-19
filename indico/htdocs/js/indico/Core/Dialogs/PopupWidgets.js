/*
 * A popup widget containing two DateSelectors where one can
 * specify a date range.
 */
type("DateRangeSelector", ["ExclusivePopupWithButtons"], {
    _drawButtons: function() {
        var self = this;

        var buttonDiv = Html.div({}, Widget.button(command(function() {
            self._submit();
        }, "Choose")));

        return buttonDiv;
    },

    _submit: function() {
        if(!this.valid) {
            return;
        }

        this.callback(this.startDate, this.endDate);
    },

    _dateFromString: function(dateStr) {
        var matches = /^(...) (\d+)\/(\d+)\/(\d+)$/.exec(dateStr);
        return new Date(matches[4], matches[3] - 1, matches[2]);
    },

    _verifyDates: function() {
        var valid = true;

        this.startDateSel.askForErrorCheck();
        this.endDateSel.askForErrorCheck();

        if (this.startDateSel.inError() || this.endDateSel.inError()) {
            valid = false;
        }
        else {
            var sDate = Util.parseJSDateTime(this.startDateSel.get(), IndicoDateTimeFormats.ServerHourless);
            var eDate = Util.parseJSDateTime(this.endDateSel.get(), IndicoDateTimeFormats.ServerHourless);

            if (sDate >= eDate) {
                valid = false;
                this.startDateSel.setError($T('Start date should be before end date'));
                this.endDateSel.setError($T('End date should be after start date'));
            }
            else {
                valid = true;
                this.startDateSel.setError(null);
                this.endDateSel.setError(null);
                this.startDate = sDate;
                this.endDate = eDate;
            }
        }

        this.valid = valid;
    },

    _drawWidget: function() {
        var self = this;

        var structure = Html.table({}, Html.tbody({},
                Html.tr("startEndDate",
                        Html.td("startEndDateEntry", "Start date:"),
                        Html.td({}, this.startDateSel.draw())),
                Html.tr("startEndDate",
                        Html.td("startEndDateEntry", "End date:"),
                        Html.td({}, this.endDateSel.draw()))));

        return Html.div({style: {width: pixels(220), height: pixels(50)}}, structure);
    },

    draw: function() {
        var self = this;
        return this.ExclusivePopupWithButtons.prototype.draw.call(this, this._drawWidget(), this._drawButtons());
    }
}, function(startDate, endDate, callback, title) {
    var self = this;

    this.valid = true;
    this.callback = callback;

    if(startDate) {
        this.startDate = this._dateFromString(startDate);
    }
    else {
        this.startDate = new Date();
    }

    if(endDate) {
        this.endDate = this._dateFromString(endDate);
    }
    else {
        this.endDate = new Date();
    }

    this.startDateSel = new DateSelector();
    this.endDateSel = new DateSelector();

    this.startDateSel.set(Util.formatDateTime(this.startDate, IndicoDateTimeFormats.ServerHourless));
    this.endDateSel.set(Util.formatDateTime(this.endDate, IndicoDateTimeFormats.ServerHourless));

    this.startDateSel.observe(function() {
        self._verifyDates();
        return true;
    });
    this.endDateSel.observe(function() {
        self._verifyDates();
        return true;
    });

    this.ExclusivePopupWithButtons(title || 'Choose date range', function() {
        self.close();
    });
});