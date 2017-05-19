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


type("TimezoneSelector", ["RemoteWidget"], {

    // Is called when the list of timezones is retrieved by AJAX.
    // Populates the select list with all timezones
    drawContent: function(select) {
        var self = this;

        var result = this.source.get();

        this.firstOption = null;
        this.nothingSelected = true;

        select.clear();

        each(result['timezones'], function(value, key) {
            var op = Html.option({value: value}, value);
            if (self.activeTZ == value) {
                self.selectedOption = op;
            }
            if (self.firstOption == null) {
                self.firstOption = op;
            }
            select.append(op);
        });

        if (this.selectTZradio.dom.checked && exists(this.selectedOption)) {
            this.selectedOption.dom.selected = true;
            this.selectTZradio.dom.value = this.selectedOption.get();
            this.nothingSelected = false;
        }
    },

    draw: function() {
        var self = this;

        // Add header
        this.div.append(Html.div({className: 'tzHeader'}, $T('Change timezone')));

        this.form = Html.form({method: "post", action: this.formTarget, style: {margin: 0}});
        this.form.append(Html.input('hidden', {name: 'csrf_token'}, $('meta[name=csrf-token]').attr('content')));
        this.div.append(this.form);

        var container = Html.div({className: 'tzContainer'});
        this.form.append(container);

        // Add the radio buttons
        this.localTZRadio = Html.input('radio', {name: 'activeTimezone'}, 'LOCAL');
        this.userTZRadio = Html.input('radio', {name: 'activeTimezone'}, 'My');
        this.selectTZradio = Html.input('radio', {name: 'activeTimezone'}, 'LOCAL');
        container.append(Html.div({style: {marginBottom: pixels(5)}}, this.localTZRadio, $T(" Use the events' local timezone ")));
        if (this.userTZ) {
            container.append(Html.div({style: {marginBottom: pixels(5)}}, this.userTZRadio, $T(" Your saved timezone"), Html.em({}, ' (' + this.userTZ + ')')));
        }
        container.append(Html.div({style: {marginBottom: pixels(5)}}, this.selectTZradio, $T(" Specify a timezone")));

        var select = Html.select({size: 12});
        this.loadingOption = Html.option({style: {color: "#444", fontStyle:'italic'}}, $T('Loading list of timezones...'));
        select.append(this.loadingOption);
        container.append(select);

        // Add all the timezones to the select list
        this.RemoteWidget('timezone.getTimezones', {}, false);
        this.RemoteWidget.prototype.draw.call(self, select);

        select.dom.onchange = function(){
            /* Save the selected timezone as radio button value */
            self.selectTZradio.dom.checked = true;
            self.selectTZradio.setAttribute('value', this.value);
        };
        this.localTZRadio.observeClick(function() {
            /* If clicked make sure no timezone is selected in the list */
            select.dom.value = "";
            select.dom.selectedIndex = -1;
            self.nothingSelected = true;
        });
        this.userTZRadio.observeClick(function() {
            /* If clicked make sure no timezone is selected in the list */
            select.dom.value = "";
            select.dom.selectedIndex = -1;
            self.nothingSelected = true;
        });
        this.selectTZradio.observeClick(function() {
            /* Make sure that there is always something selected when radio button
             * is checked */
            if (self.nothingSelected && self.firstOption) {
                self.firstOption.dom.selected = true;
                self.selectTZradio.dom.value = self.firstOption.get();
                self.nothingSelected = false;
            }
        });

        // If user is logged in add save to profile div
        if (this.userTZ) {
            container.append(Html.div({style: {fontStyle: 'italic', margin: '10px 0'}},
                    Html.input('checkbox', {name: 'saveToProfile'}), $T(' Remember these settings next time I log in')
            ));
        }

        // Add cancel and apply buttons
        var applyButton = Html.input('submit', {className: 'btn'}, $T('Apply'));
        var cancelButton = Html.input('button', {className: 'btn'}, $T('Cancel'));
        cancelButton.observeClick(function() {
            $("#timezone-selector-link").qtip('hide');
        });
        container.append(Html.div({style:{textAlign: 'center', marginTop: '15px'}}, applyButton, " ", cancelButton));
        if (this.activeTZ == 'LOCAL') {
            this.localTZRadio.set(true);
        }
        else if (this.userTZ && this.userDisplayTZMode && this.userTZ == this.activeTZ &&
                 this.userDisplayTZMode == 'MyTimezone') {
            this.userTZRadio.set(true);
        }
        else {
            this.selectTZradio.set(true);
        }
        this.alreadyDraw = true;
    },

    getContent: function(){
      if (!this.alreadyDraw){
          this.draw();
      }
      return this.div;
    }},
    /*
     * @param {String} activeTZ - the timezone currently used
     * @param {String} activeTZDisplay - the timezone displayed to the user
     * @param {String} userTZ - the timezone set in the user profile
     * @param {String} userTZDisplayMode - whether local or my timezone mode is used
     */
    function(triggerElement, activeTZ, activeTZDisplay, userTZ, userDisplayTZMode, formTarget) {
        var self = this;
        this.triggerElement = triggerElement;

        // Information about current and user timezones
        this.activeTZ = activeTZ;
        this.activeTZDisplay = activeTZDisplay;
        this.userTZ = userTZ;
        this.userDisplayTZMode = userDisplayTZMode;

        // The URL where to data should be sent when apply button is clicked
        this.formTarget = formTarget;

        this.alreadyDraw = false;


        this.div = Html.div({id: "timezonePopup", className: 'timezonePopup'});

    }
);
