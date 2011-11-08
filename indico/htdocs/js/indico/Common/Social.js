
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
            classes: 'ui-tooltip-rounded ui-tooltip-shadow social_share_tooltip' + (theme=='dark'?' ui-tooltip-dark':' ui-tooltip-blue')
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
