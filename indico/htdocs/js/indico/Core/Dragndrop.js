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

// drag and drop, table element

$.widget('indico.dragndrop', {
    // Default options
    options: {
        sortableContainer: '.sortblock', // relative to element
        sortables: '.sortblock tbody', // relative to element
        sortableElements: '> tr', // relative to sortable
        handle: '.dragHandle', // relative to sortable element - the handle to start sorting
        placeholderClass: 'dragndrop-placeholder', // the class to set on the placeholder element
        placeholderHTML: '<td></td>', // the html to put inside the placeholder element
        dropTargetClass: 'drop-target', // the class for valid drop targets (set on srrtable containers)
        noDropTargetClass: 'no-drop-target', // the class for invalid drop targets (set on srrtable containers)
        canDrop: null, // function(sortable, element) to check if <element> can be dropped on <sortable>
        onDropFail: null, // called when trying to drop an element on a nodroptarget sortable
        // Use either onUpdate or onReceive+onReorder together.
        onUpdate: null, // called when an element has been dropped
        onReceive: null, // called when an element has been dropped
        onReorder: null // called when an element has been dropped inside the same sortable
    },

    _create: function() {
        var self = this;
        var index = null; //original position of element. Used when dropping on copy mode.
        $(self.options.sortables, self.element).sortable({
            // interconnect all sortable tables
            connectWith: self.options.sortables,
            // set a class for the placeholder row
            placeholder: self.options.placeholderClass,
            // require the user to use the sorting handle to move items
            handle: self.options.handle,
            // which elements are actually sortable
            items: self.options.sortableElements,
            opacity: self.options.opacity,
            helper: self.options.helper,
            // if set to true, the item will be reverted to its new DOM position
            revert: self.options.revert,
            // triggered when sorting starts (i.e. when the user starts dragging)
            start: function(e, ui) {
                index = ui.item.index();
                if(self.options.placeholderHTML) {
                    ui.placeholder.html(self.options.placeholderHTML);
                }
                // mark all valid drop areas as targets
                $(self.options.sortables, self.element).each(function() {
                    var sortable = $(this);
                    if(!$.isFunction(self.options.canDrop) || self.options.canDrop(sortable, $(ui.item))) {
                        sortable.closest(self.options.sortableContainer).addClass(self.options.dropTargetClass);
                    }
                    else {
                        sortable.closest(self.options.sortableContainer).addClass(self.options.noDropTargetClass);
                    }
                });
            },
            // triggered when sorting finished (cancelled or successfully sorted)
            stop: function(e, ui) {
                // remove drop target highlighting
                $('.sortblock').removeClass(self.options.dropTargetClass).removeClass(self.options.noDropTargetClass);
            },
            // triggered when an element is being dropped
            receive: function(e, ui) {
                // check if we are a child of a drop target
                if(!$(this).closest('.' + self.options.dropTargetClass).length) {
                    $(ui.sender).sortable('cancel');
                    if($.isFunction(self.options.onDropFail)) {
                        $('.copy').remove();
                        self.options.onDropFail.call(self.element);
                    }
                }else {
                    $('.copy').removeClass('copy');
                    if($.isFunction(self.options.onReceive)) {
                        self.options.onReceive.call(this, ui);
                    }
                }
            },
            update: function(e, ui) {
                if($.isFunction(self.options.onUpdate)) {
                    self.options.onUpdate.call(self.element);
                }
            },
            beforeStop: function(e, ui) {
                if (ui.item.parent().get(0) == this) {
                    if($.isFunction(self.options.onReorder)) {
                        self.options.onReorder.call(this, ui);
                    }
                }

            },
            over: function(e, ui) {
                /** 2 modes:
                 *      * mode-copy: (default) the element is dropped in another sortable and kept in the origin.
                 *      * mode-move: the element is moved from the origin to the target.
                 */
                $('.copy').remove();
                var modeCopy = eval($(this).data('modeCopy'));
                if (ui.sender.get(0) != this && $.inArray(ui.sender.attr('id'), modeCopy) != -1) {
                    var clonedItem = ui.item.clone();
                    clonedItem.addClass("copy").attr('style', '').insertAfter(ui.sender.find(self.options.sortableElements+":eq("+index+")")).fadeIn("slow");
                    clonedItem.data('user', ui.item.data('user'));
                }
            }
        });
    },

    destroy: function() {
        var self = this;
        $(self.options.sortables, self.element).sortable('destroy');
        $.Widget.prototype.destroy.apply(this, arguments);
    },

    serialize: function() {
        var self = this;
        var order = {};
        $(self.options.sortables, self.element).each(function() {
            var container = $(this).closest(self.options.sortableContainer);
            var id = container.data('id');
            order[id] = [];
            $(self.options.sortableElements, this).each(function() {
                var elem = $(this);
                order[id].push(elem.data('id'));
            });
        });
        return order;
    }
});
