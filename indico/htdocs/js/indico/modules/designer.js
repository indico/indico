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

/* global AlertPopup: true */

(function(global) {
    'use strict';

    var lastSelectedDiv = null;
    var snapToGrid = false;
    // Dimensions of the template space, in pixels, and previous dimensions (cm)
    var templateDimensions, previousTemplateDimensions, pixelsPerCm, initialOffset, zoomFactor;
    // Id of the next element to be inserted
    var itemIdCounter = -1;
    // Pointer for the jQuery-UI tabs controller
    var controlTabs = null;
    var editing = false;
    var items = {};
    var itemTitles = {};

    var DEFAULT_PIXEL_CM = 50;

    function zoom(val) {
        return val * zoomFactor;
    }

    function unzoom(val) {
        return val / zoomFactor;
    }

    function _zoomFont(scalingFunction, fontSize) {
        var pattern = /([0-9.]+)pt/g;
        var ftsize = pattern.exec(fontSize)[1];
        return scalingFunction(ftsize) + 'pt';
    }

    var zoomFont = _.partial(_zoomFont, zoom);
    var unzoomFont = _.partial(_zoomFont, zoom);

    function getImageRealDimensions(img) {
        var tmpImage = new Image();
        tmpImage.src = img.attr("src");
        return {
            width: tmpImage.width,
            height: tmpImage.height
        };
    }

    function generateItemId() {
        ++itemIdCounter;
        return itemIdCounter;
    }

    function createItem(type) {
        var item = {
            id: generateItemId(),
            type: type,
            x: pixelsPerCm,
            y: initialOffset,
            font_family: "sans-serif",
            bold: false,
            italic: false,
            text_align: "center",
            color: "black",
            font_size: "15pt",
            width: (type === 'ticket_qr_code') ? 100 : 400,
            height: (type === 'ticket_qr_code') ? 100 : null,
            text: $T("Fixed text"),

            // The following attributes have no meaning to the server
            selected: false,
        };

        item.toHTML = (function() {
            var html = $('<div>').addClass('designer-item')
                                 .toggleClass('selected', this.selected)
                                 .css({
                                     width: zoom(this.width),
                                     height: this.height ? zoom(this.height) : this.height,
                                     cursor: 'move',
                                     fontWeight: this.bold ? 'bold' : 'normal',
                                     fontStyle: this.italic ? 'italic' : 'normal',
                                     fontFamily: this.font_family,
                                     fontSize: zoomFont(this.font_size),
                                     textAlign: this.text_align.replace('Justified', 'justify'),
                                     color: this.color,
                                 })
                                .attr('data-type', this.type)
                                .text(this.type === "fixed" ? this.text : itemTitles[this.type]);
            return html;
        }).bind(item);

        items[item.id] = item;
        return item;
    }

    function createItemFromObject(obj) {
        delete obj.id;
        return _.extend(createItem(), obj);
    }

    // Dimensions class
    function Dimensions(width, height) {
        this.realWidth = width;
        this.realHeight = height;
        this.width = zoom(width);
        this.height = zoom(height);
    }

    // This function creates a new draggable div
    function createDiv(item) {
        // Each div has:
        // -a unique id, which is a natural number (0, 1, 2, ...)
        // -a type (stored in the name attribute)
        // -absolute x,y position
        // -an inner HTML with its content
        var newDiv = $('<div/>').css({
            position: 'absolute',
            left: item.x + 'px',
            top: item.y + 'px',
            zIndex: itemIdCounter + 10
        }).data('id', item.id).appendTo('#template-div');

        newDiv.draggable({
            containment: '#template-div',
            stack: '#template-div > div',
            opacity: 0.5,
            drag: function(e, ui) {
                if (snapToGrid) {
                    ui.position.left = Math.floor(ui.position.left / 10) * 10;
                    ui.position.top = Math.floor(ui.position.top / 10) * 10;
                }
            },
            stop: function(e, ui) {
                var itemId = $(this).data('id');
                items[itemId].x = unzoom(ui.position.left);
                items[itemId].y = unzoom(ui.position.top);
            }
        });

        return newDiv;
    }

    // This function inserts the selected element in the blank space where template designing takes place
    function insertElement() {
        var selectedType = $('#elementList').val();
        var newItem = createItem(selectedType);
        var newDiv = createDiv(newItem);
        var itemHtml = newItem.toHTML().appendTo(newDiv);

        if (!lastSelectedDiv) {
            markSelected(itemHtml);
        }

        initialOffset += pixelsPerCm;
        initialOffset %= (templateDimensions.height - 20);
    }

    function removeElement() {
        if (lastSelectedDiv) {
            delete items[lastSelectedDiv.data('id')];
            lastSelectedDiv.remove();
            $('#selection-text').html('');
            lastSelectedDiv = null;
            $('#modify-panel').hide();
            $('#tab-format').hide();
            controlTabs.tabs('option', 'active', 0);
        }
    }

    function markSelected(selection) {
        // Change the text that says which item is selected
        var id = selection.parent('.ui-draggable').data('id');
        var item = items[id];
        $('#selection-text').html(item.type === 'fixed' ? $T.gettext('Fixed text') : itemTitles[item.type]);

        // Bring highlight to the element modification tab.
        if (controlTabs) {
            controlTabs.tabs('option', 'active', 1);
        }

        // Change the background color of the old selected item and the new selected item
        if (lastSelectedDiv) {
            var lastId = lastSelectedDiv.data('id');
            items[lastId].selected = false;
            lastSelectedDiv.find('.designer-item').removeClass('selected');
        }

        item.selected = true;
        selection.addClass('selected');
        lastSelectedDiv = selection.parent('.ui-draggable');

        $('#modify-panel').show();
        $('#tab-format').show();

        var itemStyles = _.filter([item.bold ? 'bold' : null, item.italic ? 'italic' : null]);

        // Change the selectors so that they match the properties of the item
        $('#alignment-selector').val(item.text_align);
        $('#font-selector').val(item.font_family);
        $('#size-selector').val(item.font_size);
        $('#style-selector').val(itemStyles.length ? itemStyles.join('_') : 'normal');
        $('#color-selector').val(item.color);
        $('#width_field').val(item.width / pixelsPerCm);

        if (item.type === 'fixed') {
            $('#fixed-text-container').fadeIn();
            $('#text-formatting-container').fadeIn();
            $('#fixed-text-field').val(item.text);
        } else if (item.type === 'ticket_qr_code') {
            $('#text-formatting-container').fadeOut();
            $('#fixed-text-container').fadeOut();
        } else {
            $('#text-formatting-container').fadeIn();
            $('#fixed-text-container').fadeOut();
            $('#fixed-text-field').val("");
        }
    }

    function inlineEdit(itemHTML) {
        var id = itemHTML.parent('.ui-draggable').data('id');
        var selectedItem = items[id];

        // Handle the individual cases as required.
        if (selectedItem.type === "fixed") {
            var text = prompt("Enter fixed-text value", selectedItem.text);

            if (text) {
                var div = itemHTML.parent('.ui-draggable');
                selectedItem.text = text;
                div.html(selectedItem.toHTML());
            }
        }
    }

    function updateRulers() {
        var prevWidthCm = Math.ceil(previousTemplateDimensions.width / pixelsPerCm);
        var widthCm = Math.ceil(templateDimensions.width / pixelsPerCm);
        var prevHeightCm = Math.ceil(previousTemplateDimensions.height / pixelsPerCm);
        var heightCm = Math.ceil(templateDimensions.height / pixelsPerCm);
        var i;

        if (templateDimensions.width > previousTemplateDimensions.width) {
            var hRuler = $('#horizontal-ruler');
            for (i = prevWidthCm; i < widthCm; i++) {
                $('<div class="marking"/>').attr('id', 'rulerh' + i).css({
                    width: pixelsPerCm + 'px',
                    left: (i * pixelsPerCm) + 'px',
                    top: 0
                }).html(i + 1).appendTo(hRuler);
            }
        } else if (templateDimensions.width < previousTemplateDimensions.width) {
            for (i = prevWidthCm; i > widthCm; i--) {
                $('#rulerh' + (i - 1)).remove();
            }
        }

        if (templateDimensions.height > previousTemplateDimensions.height) {
            var vRuler = $('#vertical-ruler');
            for (i = prevHeightCm; i < heightCm; i++) {
                $('<div class="marking"/>').attr('id', 'rulerv' + i).css({
                    'line-height': (pixelsPerCm / 2.0) + 'px',
                    'height': pixelsPerCm  + 'px',
                    'left': 0,
                    'top': (i * pixelsPerCm) + 'px'
                }).html(i + 1).appendTo(vRuler);
            }
        } else if (templateDimensions.height < previousTemplateDimensions.height) {
            for (i = prevHeightCm; i > heightCm; i--) {
                $('#rulerv' + (i - 1)).remove();
            }
        }
    }

    // This function displays all the items in the 'items' array on the screen
    // If there are already some items being displayed, it does not erase them
    function displayItems() {
        $.each(items, function(i, item) {
            var newDiv = createDiv(item);
            newDiv.css({
                left: zoom(item.x) + 'px',
                top: zoom(item.y) + 'px'
            });
            newDiv.append(item.toHTML());
            if (item.selected) {
                markSelected(newDiv.find('.designer-item'));
            }
        });
    }


    function changeTemplateSize(template) {
        var tpl = $('#template-div');
        tpl.width($('#badge_width').val() * pixelsPerCm);
        tpl.height($('#badge_height').val() * pixelsPerCm);
        previousTemplateDimensions.width = templateDimensions.width;
        previousTemplateDimensions.height = templateDimensions.height;
        templateDimensions = new Dimensions($('#badge_width').val() * DEFAULT_PIXEL_CM,
                                            $('#badge_height').val() * DEFAULT_PIXEL_CM);
        updateRulers();
        displayBackground(template);
    }

    function moveItem(direction) {
        var lastSelectedItem = items[lastSelectedDiv.data('id')];
        var div = lastSelectedDiv;
        ({
            left: function() {
                if (div) {
                    div.css('left', 0);
                    lastSelectedItem.x = 0;
                }
            },
            right: function() {
                if (div) {
                    div.css('left', (templateDimensions.width - div.width()) + "px");
                    lastSelectedItem.x = unzoom(templateDimensions.width - div.width());
                }
            },
            center: function() {
                if (div) {
                    div.css('left', ((templateDimensions.width - div.width()) / 2) + "px");
                    div.css('top', ((templateDimensions.height - div.height()) / 2) + "px");
                    lastSelectedItem.x = unzoom((templateDimensions.width - div.width()) / 2);
                    lastSelectedItem.y = unzoom((templateDimensions.height - div.height()) / 2);
                }
            },
            top: function() {
                if (div) {
                    div.css('top', 0);
                    lastSelectedItem.y = 0;
                }
            },
            bottom: function() {
                if (div) {
                    div.css('top', (templateDimensions.height - div.height()) + "px");
                    lastSelectedItem.y = unzoom(templateDimensions.height - div.height());
                }
            }
        })[direction]();
    }


    function setAttribute(attribute) {
        var item = items[lastSelectedDiv.data('id')];
        var div = lastSelectedDiv;

        if (!div) {
            return;
        }

        ({
            font: function() {
                item.font_family = $('#font-selector').val();
            },
            color: function() {
                item.color = $('#color-selector').val();
            },
            alignment: function() {
                item.text_align = $('#alignment-selector').val();
            },
            size: function() {
                item.font_size = $('#size-selector').val();
            },
            style: function() {
                switch ($('#style-selector').val()) {
                    case "normal":
                        item.bold = false;
                        item.italic = false;
                        break;
                    case "bold":
                        item.bold = true;
                        item.italic = false;
                        break;
                    case "italic":
                        item.bold = false;
                        item.italic = true;
                        break;
                    case "bold_italic":
                        item.bold = true;
                        item.italic = true;
                        break;
                }
            },
            text: function() {
                item.text = unescapeHTML($('#fixed-text-field').val());
                $('#fixed-text-field').val(item.text);
            },
            width: function() {
                item.width = $('#width_field').val() * pixelsPerCm;
                if (item.type === 'ticket_qr_code') {
                    item.height = item.width;
                }
            }
        })[attribute]();

        div.html(item.toHTML());
        lastSelectedDiv = div;
    }

    function save(template) {
        if ($('#template-name').val() === '') {
            new AlertPopup($T("Warning"), $T("Please choose a name for the template")).open();
            return;
        }
        var templateData = {
            template: {
                width: templateDimensions.realWidth,
                height: templateDimensions.realHeight,
                background_position: $('input[name=bg_position]:checked').val(),
                items: _.values(items).map(function(item) {
                    var itemCopy = $.extend(true, {}, item);
                    itemCopy.font_size = unzoomFont(item.font_size);
                    return item;
                })
            },
            clear_background: !template.background,
            title: $('#template-name').val(),
        };

        $.ajax({
            url: location.pathname,
            data: JSON.stringify(templateData),
            contentType: 'application/json',
            method: 'POST',
            complete: IndicoUI.Dialogs.Util.progress(),
            error: handleAjaxError,
            success: function(data) {
                handleFlashes(data, true);
            }
        });
    }

    function setBackgroundPos($background, mode) {
        var bgPosStretch = $('#bgPosStretch');
        var bgPosCenter = $('#bgPosCenter');

        if (mode === 'stretch') {
            $background.css({
                left: 0,
                top: 0
            });
            $background.height(templateDimensions.height);
            $background.width(templateDimensions.width);
            bgPosStretch.prop('checked', true);
            bgPosCenter.prop('checked', false);
        } else if (mode === 'center') {
            var imgDimensions = getImageRealDimensions($background);
            var ratio;
            $background.height(imgDimensions.height);
            $background.width(imgDimensions.width);

            if ($background.width() > templateDimensions.width || $background.height() > templateDimensions.height) {
                if ($background.width() > templateDimensions.width) {
                    ratio = templateDimensions.width / $background.width();

                    $background.width(templateDimensions.width);
                    $background.height($background.height() * ratio);
                    $background.css({
                        left: 0,
                        top: ((templateDimensions.height / 2.0) - ($background.height() / 2.0)) + 'px'
                    });
                }

                if ($background.height() > templateDimensions.height) {
                    ratio = templateDimensions.height / $background.height();

                    $background.width($background.width() * ratio);
                    $background.height(templateDimensions.height);

                    $background.css({
                        left: ((templateDimensions.width / 2.0) - ($background.width() / 2.0)) + 'px',
                        top: 0
                    });
                }
            } else {
                $background.css({
                    left: ((templateDimensions.width / 2) - (imgDimensions.width / 2)) + 'px',
                    top: ((templateDimensions.height / 2) - (imgDimensions.height / 2)) + 'px'
                });
            }

            bgPosStretch.prop('checked', false);
            bgPosCenter.prop('checked', true);
        }
    }

    function displayBackground(template) {
        $('#background').attr({
            src: template.background
        }).css({
            position: 'absolute',
            left: 0,
            top: 0,
            height: templateDimensions.height + 'px',
            width: templateDimensions.width + 'px',
            zIndex: 5
        }).on('load', function() {
            $('#loadingIcon').hide();
            $('#remove-background').removeClass('hidden');
            setBackgroundPos($(this), template.data.background_position);
        }).appendTo('#template-div');
    }

    function removeBackground(template) {
        if (template.background) {
            template.background = null;
            $('#background').remove();
            $('#remove-background').addClass('hidden');
        }
    }

    function unescapeHTML(str) {
        // taken from Prototype
        return str.replace(/<\w+(\s+("[^"]*"|'[^']*'|[^>])+)?>|<\/\w+>/gi, '')
                  .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
    }


    global.setupDesigner = function setupDesigner(template, config, placeholders) {
        editing = !!template;
        itemTitles = _.partial(_.extend, {}).apply(null, _.map(_.values(placeholders), _.property('options')));

        zoomFactor = config.zoom_factor;
        // Number of pixels per cm
        pixelsPerCm = zoom(DEFAULT_PIXEL_CM);

        // Number of pixels, both horizontal and vertical, that are between the top left corner
        // and the position where items are inserted
        initialOffset = pixelsPerCm;

        // Item class
        $(document).ready(function() {
            $('#bg-form input[type="file"]').on('change', function() {
                var $this = $(this);
                if ($this.val()) {
                    $('#upload-background').removeClass('hidden');
                } else {
                    $('#upload-background').addClass('hidden');
                }
            });

            if (template.backgroundId) {
                $('#remove-background').removeClass('hidden');
            }

            // select and inline edit
            $('#template-div').on('mousedown', '.designer-item', function() {
                markSelected($(this));
            }).on('dblclick', '.designer-item', function() {
                inlineEdit($(this));
            });

            $('#upload-background').click(function() {
                $('#bg-form').submit();
                return false;
            });

            // toggle grid/snap mode
            $('#snap_checkbox').change(function() {
                snapToGrid = this.checked;
            }).change();

            $('#bg-form').ajaxForm({
                dataType: 'json',
                iframe: false,
                success: function(data) {
                    if (data.error) {
                        new AlertPopup($T("Error"), data.error).open();
                        return;
                    }
                    if (template.background) {
                        $('#background').attr('src', '');
                    }
                    template.background = data.image_url;
                    displayBackground(template);
                }
            });

            $('input[name=bg_position]').change(function(e) {
                e.preventDefault();
                setBackgroundPos($('#background'), $(this).val());
            });

            $('#remove-background').click(function(e) {
                e.preventDefault();
                removeBackground(template);
            });

            $('.move-button').click(function(e) {
                e.preventDefault();
                var dir = $(this).data('direction');
                moveItem(dir);
            });

            $('.attrSelect').change(function() {
                var attr = $(this).data('attr');
                setAttribute(attr, config);
            });

            $('#changeTemplateSize').click(function(e) {
                e.preventDefault();
                changeTemplateSize(template);
            });

            $('#insert-button').click(function(e) {
                e.preventDefault();
                insertElement();
            });

            $('#remove-button').click(function(e) {
                e.preventDefault();
                removeElement();
            });

            $('#save-button').click(function(e) {
                e.preventDefault();
                save(template);
            });

            $('#badge_width, #badge_height').on('keyup', function() {
                changeTemplateSize(template);
            });

            $('#width_field').on('keyup', function() {
                setAttribute('width', config);
            });

            $('#fixed-text-field').on('keyup', function() {
                setAttribute('text', config);
            });

            controlTabs = $('#designer-control-tabs').tabs();
        });

        // We load the template if we are editing a template
        if (editing) {
            // We give the toHTML() method to each of the items
            templateDimensions = new Dimensions(template.data.width, template.data.height);
            $('#template-name').val(template.title);
            $('#template-div').width(templateDimensions.width)
                              .height(templateDimensions.height);
        } else {
            templateDimensions = new Dimensions(config.tpl_size[0], config.tpl_size[1]);
        }

        previousTemplateDimensions = new Dimensions(0, 0);

        $('#badge_width').val(templateDimensions.width / pixelsPerCm);
        $('#badge_height').val(templateDimensions.height / pixelsPerCm);

        updateRulers(); // creates the initial rulers
        changeTemplateSize(template);

        template.data.items.forEach(function(item) {
            createItemFromObject(item);
        });

        // This function displays the items, if any have been loaded, on the screen
        displayItems();
    };
})(window);
