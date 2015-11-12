$(document).ready(function() {
    'use strict';

    $('.event-service-row > .trigger').on('click', function() {
        var toggler = $(this);
        toggler.siblings('.event-service-details').slideToggle({
            start: function() {
                toggler.toggleClass('icon-expand icon-collapse');
            },
            duration: 'fast'
        });
    });

    $('.event-service-row-toggle').on('click', function(e) {
        e.preventDefault();
        var toggler = $(this);
        var toggler_button = $(this).parent().siblings('.trigger');
        toggler.parent().siblings('.event-service-details').slideToggle({
            start: function() {
                toggler_button.toggleClass('icon-expand icon-collapse');
            },
            duration: 'fast'
        });
    });

    var gradientLayer = $('.participant-list-wrapper > .gradient-layer');
    var heightControl = $('<div>', {'class': 'height-control'});
    gradientLayer.append(heightControl);
    var threeRowsHeight = heightControl.height();
    $('.participant-list-wrapper').toggleClass('collapsible collapsed',
        $('.participant-list').height() > threeRowsHeight);
    var initialHeight = $('.participant-list-wrapper').height();
    heightControl.remove();

    $('.participant-list-wrapper > .trigger, .participant-list-wrapper > .gradient-layer').on('click', function() {
        var toggler = $('.participant-list-wrapper > .trigger');
        var participantList = toggler.siblings('.participant-list');
        var wrapper = participantList.parent();
        if (wrapper.hasClass('collapsed')) {
            var newHeight = participantList.height();
            participantList.height(initialHeight);
            wrapper.find('.gradient-layer').fadeOut();
            wrapper.removeClass('collapsed');
            wrapper.animate({
                height: newHeight
            }, {
                duration: 'fast',
                start: function() {
                    toggler.addClass('icon-collapse').removeClass('icon-expand');
                },
                complete: function() {
                    participantList.height(newHeight);
                }
            });
        } else {
            wrapper.find('.gradient-layer').fadeIn();
            wrapper.animate({
                height: initialHeight,
            }, {
                duration: 'fast',
                start: function() {
                    toggler.removeClass('icon-collapse').addClass('icon-expand');
                },
                complete: function(){
                    wrapper.addClass('collapsed');
                }
            });
        }
    });

    function toggleNote(element, visible, immediate) {
        // Note for event
        var note = element.closest('#event-note-section');
        // Note for other elements
        if (note.length === 0) {
            note = element.closest('li').children('.note-area-wrapper');
        }
        var content = note.hasClass('togglable') ? note : note.find('.togglable');
        if (immediate) {
            content.toggle(visible);
        } else {
            content[visible === undefined ? 'slideToggle' : visible ? 'slideDown' : 'slideUp']();
        }
    }

    $('a.js-show-note-toggle').on('click', function(e) {
        e.preventDefault();
        toggleNote($(this));
    });

    $('input.js-toggle-note-cb').on('change', function(e, immediate) {
        toggleNote($(this), this.checked, immediate);
    });

    $('input.js-toggle-note-cb').trigger('change', [true]);

    $('.js-note-editor').ajaxDialog({
        title: $T("Edit minutes"),
        confirmCloseUnsaved: true,
        onClose: function(data, customData) {
            if (data || customData) {
                location.reload();
            }
        }
    });
});
