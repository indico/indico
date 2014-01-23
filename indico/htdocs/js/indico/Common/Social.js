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


function inject_facebook(appId) {
    $.getScript('//connect.facebook.net/en_US/all.js#xfbml=1', function() {
        FB.init({appId: appId, status: true, cookie: false, xfbml: true});
        FB.Event.subscribe('xfbml.render',
                           function () {
                               // when the "Like" button gets rendered, replace the
                               // "loading" message with it
                               $('#fb-loading').hide();
                               $('#fb-like').css({'visibility':'visible'});
                           });
        FB.XFBML.parse();
    });
}

$(function() {
    var theme = $('#social').data('theme');


    $('#social_button').qtip({

        style: {
            width: '420px',
            classes: 'qtip-rounded qtip-shadow social_share_tooltip' + (theme=='dark'?' qtip-dark':' qtip-blue')
        },
        position: {
            my: 'bottom right',
            at: 'top center'
        },
        content: $('#social_share'),
        show: {
            event: 'click',
            effect: function() {
                $(this).show('slide', {direction: 'down'});
            },
            target: $('#social_button')
        },
        hide: {
            event: 'unfocus click',
            fixed: true,
            effect: function() {
                $(this).fadeOut(300);
            }
        },
        events: {
            render: function(event, api) {

                $('#direct_link').click(function(e){
                    $(this).select();
                });

               inject_facebook($('#social').data('appData').facebook.appId);
                $.getScript('//apis.google.com/js/plusone.js');
                $.getScript('//platform.twitter.com/widgets.js');
            },
            hide: function(event, api) {
                $('#social').css('opacity', '');
            },
            show: function(event, api) {
                $('#social').css('opacity', 1.0);
            }
        }
    });
    $('#social').delay(200).fadeIn(1000);
});
