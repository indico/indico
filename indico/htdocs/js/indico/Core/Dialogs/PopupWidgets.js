/*
 * A popup widget containing two DateSelectors where one can
 * specify a date range.
 */
type("DateRangeSelector", ["ExclusivePopupWithButtons"], {
    _getButtons: function() {
        var self = this;
        return [
            [$T('Choose'), function() {
                self._submit()
            }],
            [$T('Cancel'), function() {
                self.close()
            }]
        ];
    },

    _submit: function() {
        if(!this._verifyDates()) {
            new AlertPopup($T('Invalid date range'), $T('The selected date range is invalid.')).open();
            return;
        }

        this.callback(this.startDate, this.endDate);
    },

    _dateFromString: function(dateStr) {
        var matches = /^(...) (\d+)\/(\d+)\/(\d+)$/.exec(dateStr);
        return new Date(matches[4], matches[3] - 1, matches[2]);
    },

    _verifyDates: function() {
        var dates = this.dateRangeWidget.daterange('getDates');
        var sDate = dates[0];
        var eDate = dates[1];

        if (sDate > eDate || (!this.allowEqual && (sDate - eDate) == 0)) {
            return false;
        }

        this.startDate = sDate;
        this.endDate = eDate;
        return true;
    },

    _drawWidget: function() {
        var self = this;
        self.dateRangeWidget = $('<div/>');
        return self.dateRangeWidget;
    },

    postDraw: function() {
        this.dateRangeWidget.daterange({
            allowPast: true,
            useFields: false,
            startDate: this.startDate,
            endDate: this.endDate,
            pickerOptions: {
                yearRange: 'c-2:c+2'
            }
        });
        return true; // refresh position
    },

    draw: function() {
        return this.ExclusivePopupWithButtons.prototype.draw.call(this, this._drawWidget(), {
            overflow: 'visible'
        });
    }
}, function(startDate, endDate, callback, title, allowEqual) {
    var self = this;

    this.callback = callback;
    this.allowEqual = allowEqual || false;
    this.dateRangeWidget = null;

    this.startDate = startDate ? this._dateFromString(startDate) : new Date();
    this.endDate = endDate ? this._dateFromString(endDate) : new Date();

    this.ExclusivePopupWithButtons(title || 'Choose date range', function() {
        self.close();
    });
});