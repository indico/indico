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

(function(global) {
    'use strict';

    global.setupLocationWidget = function setupLocationWidget(options) {
        options = $.extend(true, {
            fieldId: null,
            inheritanceAllowed: false,
            venues: null,
            venueNames: null,
            venueMap: null,
            rooms: null,
            inheritedLocationData: null,
            parent: {
                type: '',
                title: ''
            }
        }, options);

        var field = $('#' + options.fieldId);
        var helperText = field.closest('.form-field').find('.location-inheritance-field .info-helper');
        var venueInput = $('#location-venue-' + options.fieldId);
        var roomInput = $('#location-room-' + options.fieldId);
        var address = $('#location-address-' + options.fieldId);
        var usingDefault = $('#location-inheritance-' + options.fieldId);
        var hiddenData = field.val() ? JSON.parse(field.val()) : {};  // Contains all location related data sent to
                                                                      // the server
        var latestUsedField = null;
        var currentScrollPos = 0;
        var delta = 0;
        var validRoom = false;
        var validVenue = false;
        var preventGuessing = false;
        var roomJustCleared = false;
        var venueJustChanged = false;

        function initializeInputs() {
            address.val(hiddenData.address);
            roomInput.val(hiddenData.room_name);
            venueInput.val(hiddenData.venue_name);
            if (hiddenData.venue_id) {
                highlightOption(venueInput, venueInput.val());
            }
            if (hiddenData.room_id) {
                highlightOption(roomInput, roomInput.val());
            }
            if (options.inheritanceAllowed) {
                usingDefault.prop('checked', hiddenData.inheriting);
            }
        }

        function toggleDefaultLocation(isChecked, isInitStep) {
            if (!options.inheritanceAllowed) {
                return;
            }
            var message = $T.gettext('Using default location from: {0} ({1})').format(options.parent.title, options.parent.type);
            var text = isChecked ? message : $T.gettext('Using custom location');
            helperText.attr('title', text);
            venueInput.prop('disabled', isChecked).toggleClass('disabled', isChecked);
            roomInput.prop('disabled', isChecked).toggleClass('disabled', isChecked);
            address.prop('disabled', isChecked).toggleClass('disabled', isChecked);
            field.closest('.i-location-field').toggleClass('disabled', isChecked);

            hiddenData.inheriting = isChecked;
            field.val(JSON.stringify(hiddenData));

            /* Prefill the disabled inputs with the inherited location when the default location is checked
            (clear them otherwise) */
            if (options.inheritedLocationData !== null) {
                if (!isInitStep) {
                    if (isChecked) {
                        hiddenData = $.extend({}, options.inheritedLocationData);
                        hiddenData.inheriting = true;
                        initializeInputs();
                    } else {
                        clearField(venueInput);
                        address.val('');
                        delete hiddenData.address;
                    }
                    field.val(JSON.stringify(hiddenData)).trigger('change');
                }
            }
        }

        function reorderCategories(venueName) {
            /* When the choice of venue changes, the rooms of the selected venue need to appear on the top of the
            room typeahead list, simply by updating the groupOrder option, moving the selected venue to the first
            position of the array. */
            var groupOrder = [venueName];
            for (var i = options.venueNames.length - 1; i >= 0; i--) {
                if (!~groupOrder.indexOf(options.venueNames[i])) {
                    groupOrder.push(options.venueNames[i]);
                }
            }
            global.Typeahead[roomInput.selector].options.groupOrder = groupOrder;
        }

        function updateVenueOnRoomChange(item) {
            /* Override the venue based on the room selection */
            if (item.venue_id != hiddenData.venue_id) {
                venueJustChanged = true;
                var venueName = item.group || options.venueMap[item.venue_id];
                var data = {item_name: venueName, venue_id: item.venue_id, room_id: item.id};
                venueInput.val(venueName).trigger('typeahead:click-on-option', data);
            }
        }

        function clearRoom() {
            delete hiddenData.room_id;
            delete hiddenData.room_name;
            roomInput.val('');
            roomInput.siblings('.keyword-highlighter').removeClass('visible');
            roomJustCleared = true;
            postSelectionActions(roomInput, '');
        }

        function clearVenue() {
            delete hiddenData.venue_id;
            delete hiddenData.venue_name;
            venueInput.val('');
            venueInput.siblings('.keyword-highlighter').removeClass('visible');
            venueJustChanged = true;
            postSelectionActions(venueInput, '');
            clearRoom();
        }

        function clearField(field) {
            if (field[0].id == venueInput[0].id) {
                clearVenue();
            } else if (field[0].id == roomInput[0].id) {
                clearRoom();
            }
        }

        function updateResultsList(node, resultHtmlList) {
            /* Make sure the result dropdown is displayed just below the input field */
            var resultsWrapper = node.siblings('.typeahead__result');
            resultsWrapper.css('top', node.outerHeight() + 'px');

            /* Create/delete the 'just-use' option based on the input */
            var justUse = node.parent().find('.just-use-option');
            if (node.val()) {
                if (!justUse.length) {
                    justUse = $('<div>', {
                        'class': 'just-use-option'
                    });
                    var justUseLink = $('<a>').on('click', function() {
                        node.trigger('typeahead:click-on-custom-option', {item_name: node.val()});
                    });
                    justUse.append(justUseLink);
                    resultsWrapper.append(justUse);
                }
                justUse.find('a').text($T.gettext('Just use "{0}"').format(node.val()));
            } else {
                justUse.remove();
            }

            /* Always mark the first option as active in order for the keyboard inputs to work */
            var firstOption = resultHtmlList.find('li.typeahead__item').first();
            if (!firstOption.length) {
                node.parent().find('.just-use-option').addClass('active');
            } else {
                resultHtmlList.find('li.typeahead__item').first().addClass('active');
            }
            return resultHtmlList;
        }

        function scrollResultsList(inputField) {
            var parent = inputField.parent();
            var activeOption = parent.find('.typeahead__result').find('.typeahead__item.active');
            var dropdownList = parent.find('.typeahead__list');
            if (activeOption.length != 0) {
                if (activeOption.position().top + activeOption.outerHeight() > dropdownList.outerHeight()) {
                    delta = activeOption.position().top + activeOption.outerHeight() - dropdownList.outerHeight();
                    currentScrollPos += delta;
                    dropdownList.animate({
                        scrollTop: currentScrollPos
                    }, 50);
                } else if (activeOption.position().top < dropdownList.position().top){
                    currentScrollPos += activeOption.position().top;
                    dropdownList.animate({
                        scrollTop: currentScrollPos
                    }, 50);
                }
            }
            parent.find('.just-use-option').toggleClass('active', !activeOption.length);
        }

        function postSelectionActions(inputField, value) {
            field.val(JSON.stringify(hiddenData)).trigger('change');
            if (inputField[0].id == venueInput[0].id) {
                latestVenueValue = value;
            } else if (inputField[0].id == roomInput[0].id) {
                latestRoomValue = value;
            }
        }

        function highlightOption(inputField, value) {
            var highlighter = inputField.siblings('.keyword-highlighter');
            highlighter.html(value).addClass('visible');
        }

        function cleanQuery(query) {
            return query ? query.trim() : '';
        }

        function findRoomInVenue(query, venue) {
            if (options.rooms[venue]) {
                return $.grep(options.rooms[venue].data, function(room) {
                    return room.name.toUpperCase() == query.toUpperCase();
                });
            }
            return [];
        }

        function toggleOpenResultsList(inputField) {
            if (inputField[0].id == venueInput[0].id && roomInput.closest('.typeahead__container').hasClass('result')) {
                roomInput.trigger('typeahead:close-results-list');
            } else if (inputField[0].id == roomInput[0].id && venueInput.closest('.typeahead__container').hasClass('result')) {
                venueInput.trigger('typeahead:close-results-list');
            }
        }

        function resetSelectedOption() {
            if (latestUsedField[0].id == venueInput[0].id) {
                validVenue = true;
                venueInput.val(latestVenueValue);
                if (hiddenData.venue_id) {
                    highlightOption(venueInput, latestVenueValue);
                }
            } else if (latestUsedField[0].id == roomInput[0].id) {
                validRoom = true;
                roomInput.val(latestRoomValue);
                if (hiddenData.room_id) {
                    highlightOption(roomInput, latestRoomValue);
                }
            }
        }

        function handleKeystrokes(node) {
            node.on('keydown', function(evt) {
                var $this = $(this);
                var typeaheadField = $this.parent();
                var resultsAreOpen = typeaheadField.parent().hasClass('result');
                var activeItem = typeaheadField.find('.active');
                if ((evt.keyCode == K.TAB || evt.keyCode == K.ENTER) && activeItem.length && resultsAreOpen) {
                    preventGuessing = true;
                    if(evt.keyCode == K.ENTER) {
                        evt.preventDefault();
                    }
                    evt.stopImmediatePropagation();
                    activeItem.find('a').click();
                }
                else if (evt.keyCode == K.TAB && node.val()) {
                    evt.stopImmediatePropagation();
                }
                else if (evt.keyCode == K.ESCAPE) {
                    evt.preventDefault();
                    evt.stopImmediatePropagation();
                    resetSelectedOption();
                    $this.trigger('typeahead:close-results-list');
                }
            });
        }

        initializeInputs();

        var latestVenueValue = venueInput.val();
        var latestRoomValue = roomInput.val();

        if (options.inheritanceAllowed) {
            usingDefault.on('click', function () {
                toggleDefaultLocation(this.checked);
            });
            toggleDefaultLocation(usingDefault.prop('checked'), true);
        }

        venueInput.typeahead({
            source: options.venues,
            minLength: 0,
            searchOnFocus: true,
            resultContainer: '#' + venueInput.siblings('.typeahead__result').find('.results-list-container').attr('id'),
            template: '<span id="location-venue-{{id}}">{{name}}</span>',
            // Used to keep the dropdown list open while there are no results (required by the 'just-use' option)
            emptyTemplate: function() { return ''; },
            display: 'name',
            hint: true,
            cancelButton: false,
            callback: {
                onInit: function(node) {
                    this.query = this.rawQuery = node.val();  // Updates the results dropdown on init
                    handleKeystrokes(node);
                },
                onClickBefore: function() {
                    // Used in the onHideLayout callback to identify the reason of the dropdown closure
                    validVenue = true;
                },
                onClickAfter: function(node, a, item) {
                    venueInput.trigger('typeahead:click-on-option', {
                        item_name: item.name,
                        venue_id: item.id
                    });
                },
                onLayoutBuiltBefore: function(node, query, result, resultHtmlList) {
                    return updateResultsList(node, resultHtmlList);
                },
                onSearch: function(node, query) {
                    this.query = cleanQuery(query);
                },
                onShowLayout: function() {
                    toggleOpenResultsList(this.node);
                    venueInput.siblings('.keyword-highlighter').removeClass('visible');
                    currentScrollPos = 0;
                },
                onHideLayout: function(node) {
                    var venueValue = venueInput.val();
                    if (!validVenue && node.val() && !preventGuessing) {
                        /* Try to guess the choice of the user in case the results dropdown closes without a
                        selection (i.e. clicking outside). If an exact match is found, select it, otherwise
                        use the 'just-use' option */
                        var result = $.grep(options.venues.data, function(venue) {
                            return venue.name.toUpperCase() == venueValue.toUpperCase();
                        });
                        if (result.length) {
                            venueInput.trigger('typeahead:click-on-option', {
                                item_name: result[0].name,
                                venue_id: result[0].id
                            });
                        } else {
                            venueInput.trigger('typeahead:click-on-custom-option', {item_name: venueValue});
                        }
                    } else if (!node.val()) {
                        clearField(venueInput);
                    }
                    preventGuessing = false;
                    validVenue = false;
                },
                onResult: function(node, query, result, resultCount) {
                    node.parent().find('.just-use-option').toggleClass('active', !resultCount);
                }
            }
        });

        roomInput.typeahead({
            source: options.rooms,
            minLength: 0,
            searchOnFocus: true,
            group: true,
            hint: true,
            cancelButton: false,
            maxItem: 0,
            resultContainer: '#' + roomInput.siblings('.typeahead__result').find('.results-list-container').attr('id'),
            template: '<span id="location-room-{{id}}">{{name}}</span>',
            emptyTemplate: function() { return ''; },
            display: 'name',
            callback: {
                onInit: function(node) {
                    this.query = this.rawQuery = node.val();
                    handleKeystrokes(node);
                },
                onClickBefore: function() {
                    validRoom = true;
                },
                onClickAfter: function(node, a, item) {
                    roomInput.trigger('typeahead:click-on-option', item);
                },
                onLayoutBuiltBefore: function(node, query, result, resultHtmlList) {
                    return updateResultsList(node, resultHtmlList);
                },
                onSearch: function(node, query) {
                    this.query = cleanQuery(query);
                },
                onShowLayout: function() {
                    toggleOpenResultsList(this.node);
                    roomInput.siblings('.keyword-highlighter').removeClass('visible');
                    currentScrollPos = 0;
                },
                onHideLayout: function(node) {
                    if (!validRoom && node.val() && !preventGuessing) {
                        var result = [];
                        var venueValue = venueInput.val();
                        var roomValue = roomInput.val();
                        if (venueValue) {
                            result = findRoomInVenue(roomValue, venueValue);
                        } else {
                            for (var i = 0; i < options.venueNames.length && !result.length; i++) {
                                result = findRoomInVenue(roomValue, options.venueNames[i]);
                            }
                        }
                        if (result.length) {
                            roomInput.trigger('typeahead:click-on-option', result[0]);
                        } else {
                            roomInput.trigger('typeahead:click-on-custom-option', {item_name: roomValue});
                        }
                    } else if (!node.val()) {
                        clearField(roomInput);
                    }
                    preventGuessing = false;
                    validRoom = false;
                },
                onResult: function(node, query, result, resultCount) {
                    node.parent().find('.just-use-option').toggleClass('active', !resultCount);
                }
            }
        });

        venueInput.on('typeahead:click-on-option', function(e, data) {
            reorderCategories(data.item_name);
            /* The room needs to be cleared when the venue changes */
            if (hiddenData.venue_id && data.venue_id != hiddenData.venue_id && !data.room_id) {
                clearField(roomInput);
            }
            hiddenData.venue_name = data.item_name;
            hiddenData.venue_id = data.venue_id;
            postSelectionActions(venueInput, data.item_name);
            highlightOption(venueInput, data.item_name);
            venueInput.attr('title', data.item_name);
        })
        .on('typeahead:click-on-custom-option', function(e, data) {
            if (hiddenData.room_id) {
                clearField(roomInput);
            }
            delete hiddenData.venue_id;
            hiddenData.venue_name = data.item_name;
            postSelectionActions(venueInput, data.item_name);
            venueInput.val(data.item_name);
            validVenue = true;
            venueInput.attr('title', data.item_name);
            venueInput.focus();
            venueInput.trigger('typeahead:close-results-list');
        });

        roomInput.on('typeahead:click-on-option', function(e, data) {
            updateVenueOnRoomChange(data);
            hiddenData.room_id = data.id;
            delete hiddenData.room_name;
            postSelectionActions(roomInput, data.name);
            highlightOption(roomInput, data.name);
            roomInput.attr('title', data.name);
        }).on('typeahead:click-on-custom-option', function(e, data) {
            delete hiddenData.room_id;
            hiddenData.room_name = data.item_name;
            postSelectionActions(roomInput, data.item_name);
            roomInput.val(data.item_name);
            validRoom = true;
            roomInput.attr('title', data.item_name);
            roomInput.focus();
            roomInput.trigger('typeahead:close-results-list');
        });

        $('#' + options.fieldId + '-wrapper .i-location-input-field').on('typeahead:close-results-list', function() {
            global.Typeahead["#" + this.id].hideLayout();
        }).on('typeahead:open-results-list', function() {
            global.Typeahead["#" + this.id].showLayout();
        })
        .on('focus.typeahead', function() {
            /* In case the input is cleared, this ensures that the results dropdown will contain all available
            options. */
            var $this = $(this);
            if (roomJustCleared && $this[0].id == roomInput[0].id) {
                $this.trigger('input.typeahead');
                roomJustCleared = false;
            }
            if (venueJustChanged && $this[0].id == venueInput[0].id) {
                $this.trigger('input.typeahead');
                venueJustChanged = false;
            }
            // Make sure the results dropdown are displayed above the dialog.
            field.closest('.ui-dialog-content').css('overflow', 'inherit');
            field.closest('.exclusivePopup').css('overflow', 'inherit');

            latestUsedField = $(this);
        })
        .on('keydown', function(evt) {
            if (~[K.UP, K.DOWN].indexOf(evt.keyCode)) {
                var $this = $(this);
                scrollResultsList($this);
                $this.trigger('focus.typeahead');
            }
        })
        .on('click', function() {
            /* Since focus remains on the field after selection, we need special handling for the click event in
            order to reopen the results list */
            if (!$(this).closest('.typeahead__container').hasClass('result')) {
                $(this).trigger('focus.typeahead').trigger('input');
            }
        });

        $('#' + options.fieldId + '-wrapper .toggle-results-list').on('click', function() {
            var container = $(this).parent().parent();
            var input = container.find('.i-location-input-field').eq(0);
            input.trigger(container.hasClass('result') ? 'typeahead:close-results-list' : 'focus.typeahead');
        });

        address.on('keyup input', function() {
            hiddenData.address = address.val();
            field.val(JSON.stringify(hiddenData)).trigger('change');
        });

        $('#' + options.fieldId + '-wrapper .keyword-highlighter').on('click', function() {
            /* Focus will trigger the results dropdown to open */
            $(this).parent().find('.i-location-input-field').eq(0).trigger('focus.typeahead');
        });
    };
})(window);
