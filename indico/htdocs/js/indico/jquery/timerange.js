/* This file is part of Indico.
 * Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
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

(function($) {
    $.widget('indico.timerange', {
        options: {
            label: $T('Time'),
            initStartTime: '0:00',
            initEndTime: '23:59',
            startTimeName: 'start_time',
            endTimeName: 'end_time',
            wrapInToolbar: true,
            thinToolbar: true,
            errorHighlight: true
        },

        _create: function() {
            var self = this;
            var element = self.element;
            var opt = self.options;

            self._createInputs();
            self._createSlider();

            var thin = '';
            if (opt.thinToolbar) {
                thin = 'thin';
            }

            if (opt.wrapInToolbar) {
                var toolbar = $('<div class="toolbar {0}"/>'.format(thin));
                element.append(toolbar);
            } else {
                var toolbar = element;
            }

            var group = $('<div class="group with-slider timerange"/>');
            var label = $('<span class="i-button label heavy"/>').text(opt.label);
            var range = $('<span class="i-button label slider"/>').append(self.slider);

            group.append(label)
                .append(self.startTime)
                .append(range)
                .append(self.endTime)
                .appendTo(toolbar);
        },

        _createInputs: function() {
            var self = this;
            var element = self.element;
            var opt = self.options;

            var typeWatchOptions = {
                captureLength: 0,
                highlight: false,
                wait: 250,
                callback: function() {
                    self._updateSlider();
                }
            }

            self.startTime = $('<input type="text" name="{0}" maxlength="5"/>'.format(opt.startTimeName))
                .val(opt.initStartTime)
                .typeWatch(typeWatchOptions);
            self.endTime = $('<input type="text" name="{0}" maxlength="5"/>'.format(opt.endTimeName))
                .val(opt.initEndTime)
                .typeWatch(typeWatchOptions);
        },

        _createSlider: function() {
            var self = this;
            var element = self.element;
            var opt = self.options;

            self.slider = $('<span/>').slider({
                range: true,
                max: 1439,  // last minute in a day
                values: [
                    self.__getTime(opt.initStartTime),
                    self.__getTime(opt.initEndTime)
                ],
                step: 5,
                start: function(e, ui) {
                    self._updateInputs(e, ui);
                },
                slide: function(e, ui) {
                    self._updateInputs(e, ui);
                }
            });
        },

        _updateInputs: function(event, ui) {
            var self = this;

            self._restoreHighlight();
            self.startTime.val(self.__getTimeString(ui.values[0]));
            self.endTime.val(self.__getTimeString(ui.values[1]));
        },

        _updateSlider: function() {
            var self = this;

            self._restoreHighlight();
            if (self.validate()) {
                console.log('hi');
                var sTime = self.__getTime(self.startTime.val());
                var eTime = self.__getTime(self.endTime.val());
                self.slider.slider('values', 0, sTime).slider('values', 1, eTime);
            }
        },

        _restoreHighlight: function() {
            var self = this;

            self.startTime.removeClass('hasError');
            self.endTime.removeClass('hasError');
        },

        __getTimeString: function(time) {
            var minutes = parseInt(time % 60);
            var hours = parseInt(time / 60 % 24);

            minutes = minutes + '';
            if (minutes.length == 1) {
                minutes = '0' + minutes;
            }

            return hours + ':' + minutes;
        },

        __getTime: function(timeString) {
            var time = timeString.split(':');
            return (Math.min(parseInt(time[0]), 23) * 60) + Math.min(parseInt(time[1]), 59);
        },

        __validateTime: function(timeString) {
            var time = timeString.split(':');
            var hours = parseInt(time[0]);
            var minutes = parseInt(time[1]);

            if (isNaN(hours) || isNaN(minutes)) {
                return false;
            }

            if (hours > 23 || minutes > 59) {
                return false;
            }

            return true;
        },

        getStartTime: function() {
            var self = this;
            return self.startTime.val();
        },

        getEndTime: function() {
            var self = this;
            return self.endTime.val();
        },

        resetRange: function() {
            var self = this;

            self.startTime.val(self.options.initStartTime);
            self.endTime.val(self.options.initEndTime);
            self._updateSlider();
        },

        setStartTime: function(time) {
            var self = this;

            self.startTime.val(time);
            self._updateSlider();
        },

        setEndTime: function(time) {
            var self = this;

            self.endTime.val(time);
            self._updateSlider();
        },

        setMaxRange: function() {
            var self = this;

            self.startTime.val('0:00');
            self.endTime.val('23:59');
            self._updateSlider();
        },

        setMinRange: function() {
            var self = this;

            self.startTime.val('0:00');
            self.endTime.val('0:00');
            self._updateSlider();
        },

        validate: function(highlight) {
            var self = this;

            var valid = true;
            var re = /\d{1,2}:\d{2}/;
            var sTime = self.startTime.val();
            var eTime = self.endTime.val();

            if (highlight === undefined) {
                highlight = self.options.errorHighlight;
            }

            if (!sTime.match(re) || !self.__validateTime(sTime)) {
                valid = false;
                if (highlight) {
                    self.startTime.addClass('hasError');
                }
            }

            if (!eTime.match(re) || !self.__validateTime(eTime)) {
                valid = false;
                if (highlight) {
                    self.endTime.addClass('hasError');
                }
            }

            return valid;
        },
    })
})(jQuery);
