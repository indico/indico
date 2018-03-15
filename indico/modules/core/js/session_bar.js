/* This file is part of Indico.
 * Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

(function() {
    'use strict';

    function setupProtection() {
        $('#protection-details-link').qtip({
            style: {
                width: '280px',
                classes: 'qtip-rounded qtip-shadow qtip-popup',
                tip: {
                    corner: true,
                    width: 20,
                    height: 15
                }
            },
            position: {
                my: 'top center',
                at: 'bottom center'
            },
            content: $('#protection-details'),
            show: {
                event: 'click',
                effect: function() {
                    $(this).fadeIn(300);
                }
            },
            hide: {
                event: 'unfocus click',
                fixed: true,
                effect: function() {
                    $(this).fadeOut(300);
                }
            }
        });
    }

    function setupTimezone() {
        var widget = $('#tz-selector-widget');
        widget.on('change', 'input[name=tz_mode]', function() {
            var customTZ = this.value === 'custom';
            var customTZSelect = widget.find('select[name=tz]');
            customTZSelect.prop('disabled', !customTZ);
            if (customTZ) {
                customTZSelect.focus();
                scrollToCurrentTZ();
            }
        });

        $('#tz-selector-link').qtip({
            style: {
                width: '300px',
                classes: 'qtip-rounded qtip-shadow qtip-popup qtip-timezone',
                tip: {
                    corner: true,
                    width: 20,
                    height: 15
                }
            },
            position: {
                my: 'top center',
                at: 'bottom center'
            },
            content: widget,
            show: {
                event: 'click',
                effect: function() {
                    $(this).fadeIn(300);
                }
            },
            hide: {
                event: 'unfocus click',
                fixed: true,
                effect: function() {
                    $(this).fadeOut(300);
                }
            },
            events: {
                show: function() {
                    _.defer(scrollToCurrentTZ);
                }
            }
        });

        function scrollToCurrentTZ() {
            var option = widget.find('select[name=tz] option:selected')[0];
            if (option) {
                option.scrollIntoView(false);
            }
        }
    }

    function setupUserSettings() {
        var link = $('#user-settings-link');

        $('#user-settings-widget a:not([data-toggle=dropdown])').on('click', function() {
            link.qtip('hide');
        });

        link.qtip({
            style: {
                minWidth: '200px',
                classes: 'qtip-rounded qtip-shadow qtip-popup qtip-allow-overflow',
                tip: {
                    corner: true,
                    width: 20,
                    height: 15
                }
            },
            position: {
                my: 'top center',
                at: 'bottom center'
            },
            content: $('#user-settings-widget'),
            show: {
                event: 'click',
                effect: function() {
                    $(this).fadeIn(300);
                }
            },
            hide: {
                event: 'unfocus click',
                fixed: true,
                effect: function() {
                    $(this).fadeOut(300);
                }
            }
        });
    }

    $(document).ready(function() {
        setupProtection();
        setupTimezone();
        setupUserSettings();
    });
})();
