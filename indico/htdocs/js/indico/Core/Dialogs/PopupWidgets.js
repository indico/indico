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
        return new Date(dateStr);
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

    if (startDate && typeof startDate == 'string') {
        startDate = this._dateFromString(startDate);
    }
    if (endDate && typeof endDate == 'string') {
        endDate = this._dateFromString(endDate);
    }

    this.startDate = startDate || new Date();
    this.endDate = endDate || new Date();

    this.ExclusivePopupWithButtons(title || 'Choose date range', function() {
        self.close();
    });
});
