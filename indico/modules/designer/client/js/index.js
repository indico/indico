// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global alertPopup:false,confirmPrompt:false, handleAjaxError:false, handleFlashes:false,
          ajaxDialog:false */
/* eslint-disable max-len, no-var, object-shorthand, prefer-template */

import _ from 'lodash';

import {$T} from 'indico/utils/i18n';

(function(global) {
  var snapToGrid = false;
  // Dimensions of the template space, in pixels, and previous dimensions (cm)
  var templateDimensions, previousTemplateDimensions, pixelsPerCm, initialOffset, zoomFactor;
  // Id of the next element to be inserted
  var itemIdCounter = -1;
  // Pointer for the jQuery-UI tabs controller
  var editing = false;
  var items = {};
  var backsideItems = {};
  var backsideTemplateID = null;
  var itemTitles = {};
  var initialWidth = null;
  var initialHeight = null;
  var showConfirmationDialog = false;
  var confirmMessage = $T.gettext(
    'The back side of the templates that use this one as the back side will be removed.'
  );
  var confirmTitle = $T.gettext('Disassociate back sides');
  var removeBackSide = false;

  var DEFAULT_PIXEL_CM = 50;

  let imageTypes = null;

  let images = null;

  let lastSelectedItem = null;

  function isImage(type) {
    return imageTypes.includes(type);
  }

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
    tmpImage.src = img.attr('src');
    return {
      width: tmpImage.width,
      height: tmpImage.height,
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
      font_family: 'sans-serif',
      bold: false,
      italic: false,
      text_align: 'center',
      color: '#000000',
      background_color: null,
      font_size: '15pt',
      width: isImage(type) ? 150 : 400,
      height: isImage(type) ? 150 : null,
      text: $T('Fixed text'),
      zIndex: itemIdCounter + 10,

      // The following attributes have no meaning to the server
      selected: false,
    };

    item.toHTML = function() {
      var html = $('<div>')
        .addClass('designer-item')
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
          backgroundColor: this.background_color,
          zIndex: this.zIndex,
        })
        .attr('data-type', this.type)
        .text(
          this.type === 'fixed'
            ? this.text
            : this.type === 'fixed_image' && this.image_id
            ? ''
            : itemTitles[this.type]
        );
      return html;
    }.bind(item);

    return item;
  }

  function createItemFromObject(obj, isBackside) {
    delete obj.id;
    var newItem = _.extend(createItem(), obj);
    if (!isBackside) {
      items[newItem.id] = newItem;
    } else {
      backsideItems[newItem.id] = newItem;
    }

    return newItem;
  }

  // Dimensions class
  function Dimensions(width, height) {
    this.realWidth = width;
    this.realHeight = height;
    this.width = zoom(width);
    this.height = zoom(height);
  }

  // This function creates a new draggable div
  function createDiv(item, isBackside) {
    // Each div has:
    // -a unique id, which is a natural number (0, 1, 2, ...)
    // -a type (stored in the name attribute)
    // -absolute x,y position
    // -an inner HTML with its content
    var templateSide = isBackside ? '.template-side.back' : '.template-side.front';
    var newDiv = $('<div/>')
      .css({
        position: 'absolute',
        left: item.x + 'px',
        top: item.y + 'px',
        zIndex: item.zIndex,
      })
      .data('id', item.id)
      .attr('data-id', item.id)
      .appendTo(templateSide);

    if (isBackside) {
      return newDiv;
    }

    newDiv.draggable({
      containment: templateSide,
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
      },
    });

    return newDiv;
  }

  // This function inserts the selected element in the blank space where template designing takes place
  function insertElement() {
    var selectedType = $('#element-list').val();
    var newItem = createItem(selectedType);
    var newDiv = createDiv(newItem);
    var itemHtml = newItem.toHTML().appendTo(newDiv);

    items[newItem.id] = newItem;
    selectItem(itemHtml);
    initialOffset += pixelsPerCm;
    initialOffset %= templateDimensions.height - 20;
  }

  function removeSelectedElement() {
    var $selectedItem = $('.designer-item.selected');
    var selectedItem = getSelectedItemData();

    if (selectedItem) {
      delete items[selectedItem.id];
      $selectedItem.remove();
      $('.element-tools').addClass('hidden');
    }
  }

  function getItemData($item, isBackside) {
    if ($item.length) {
      var id = $item.closest('.ui-draggable').data('id');
      return isBackside ? backsideItems[id] : items[id];
    }
    return;
  }

  function getSelectedItemData() {
    var $selectedItem = $('.designer-item.selected');
    return getItemData($selectedItem);
  }

  function deselectItem($item) {
    var item = getItemData($item);
    if (item) {
      item.selected = false;
      $item.removeClass('selected');
    }
  }

  function selectItem($item) {
    var item = getItemData($item);

    $('.element-tools').removeClass('hidden');
    $('.second-row').removeClass('disappear');
    $('.selection-text').html(itemTitles[item.type]);

    if (item.type === 'fixed_image') {
      $('.js-remove-img').prop('disabled', !item.image_id);
    }
    const $imageFile = $('#imageFile');
    $('.js-upload-img').prop('disabled', !$imageFile.val());

    deselectItem($('.designer-item.selected'));
    item.selected = true;
    $item.addClass('selected');

    var itemStyles = _.filter([item.bold ? 'bold' : null, item.italic ? 'italic' : null]);

    // Change the selectors so that they match the properties of the item
    $('#text-color-selector').val(item.color);
    const textColorPreview = $('#text-color-preview');
    textColorPreview.toggleClass('no-value', !item.color);
    textColorPreview.css({backgroundColor: item.color});
    $('#bg-color-selector').val(item.background_color);
    const bgColorPreview = $('#bg-color-preview');
    bgColorPreview.toggleClass('no-value', !item.background_color);
    bgColorPreview.css({backgroundColor: item.background_color});
    $('#alignment-selector').val(item.text_align);
    $('#font-selector').val(item.font_family);
    $('#size-selector').val(item.font_size);
    $('#style-selector').val(itemStyles.length ? itemStyles.join('_') : 'normal');
    $('.js-element-width').val(item.width / pixelsPerCm);
    $('.js-element-height').val(item.height / pixelsPerCm);

    var $fixedTextField = $('#fixed-text-field');
    const $itemHeightField = $('#subtool-element-height');
    var $fontTools = $('.font-tools');
    var $fixedImageTool = $('#fixed-image-tool');

    if (item.type === 'fixed') {
      $fontTools.show();
      $fixedTextField.closest('.tool').show();
      $fixedTextField.val(item.text);
      $itemHeightField.hide();
      $fixedImageTool.hide();
    } else if (isImage(item.type)) {
      $fontTools.hide();
      $fixedTextField.closest('.tool').hide();
      $itemHeightField.show();
      $fixedImageTool.hide();
      if (item.type === 'fixed_image') {
        $fixedImageTool.show();
      }
    } else {
      $fontTools.show();
      $fixedTextField.closest('.tool').hide();
      $fixedTextField.val('');
      $itemHeightField.hide();
      $fixedImageTool.hide();
    }
  }

  function inlineEditItem($item) {
    var item = getItemData($item);

    // Handle the individual cases as required.
    if (item.type === 'fixed') {
      var text = prompt('Enter fixed-text value', item.text); // eslint-disable-line no-alert

      if (text) {
        var div = $item.parent('.ui-draggable');
        item.text = text;
        div.html(item.toHTML());
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
        $('<div class="marking"/>')
          .attr('id', 'rulerh' + i)
          .css({
            width: pixelsPerCm + 'px',
            left: i * pixelsPerCm + 'px',
            top: 0,
          })
          .html(i + 1)
          .appendTo(hRuler);
      }
    } else if (templateDimensions.width < previousTemplateDimensions.width) {
      for (i = prevWidthCm; i > widthCm; i--) {
        $('#rulerh' + (i - 1)).remove();
      }
    }

    if (templateDimensions.height > previousTemplateDimensions.height) {
      var vRuler = $('#vertical-ruler');
      for (i = prevHeightCm; i < heightCm; i++) {
        $('<div class="marking"/>')
          .attr('id', 'rulerv' + i)
          .css({
            'line-height': pixelsPerCm / 2.0 + 'px',
            'height': pixelsPerCm + 'px',
            'left': 0,
            'top': i * pixelsPerCm + 'px',
          })
          .html(i + 1)
          .appendTo(vRuler);
      }
    } else if (templateDimensions.height < previousTemplateDimensions.height) {
      for (i = prevHeightCm; i > heightCm; i--) {
        $('#rulerv' + (i - 1)).remove();
      }
    }
  }

  // This function displays all the items in the 'items' array on the screen
  // If there are already some items being displayed, it does not erase them
  function displayItems(isBackside) {
    var itemsList = isBackside ? backsideItems : items;
    $.each(itemsList, function(i, item) {
      var newDiv = createDiv(item, isBackside);
      newDiv.css({
        left: zoom(item.x) + 'px',
        top: zoom(item.y) + 'px',
        zIndex: item.zIndex,
      });
      newDiv.append(item.toHTML());
      if (item.type === 'fixed_image' && item.image_id) {
        const $imageElement = createFixedImageElement(item);
        $imageElement.appendTo(newDiv.find('.designer-item'));
      }
      if (item.selected && !isBackside) {
        selectItem(newDiv.find('.designer-item'));
      }
    });
  }

  function updatePreset(templateWidth, templateHeight) {
    $('.js-preset-tool option').each(function() {
      var $this = $(this);

      if ($this.val() === 'custom') {
        return;
      }

      var width = $this.data('width');
      var height = $this.data('height');

      if (width === templateWidth && height === templateHeight) {
        $this.prop('selected', true);
        $('.js-template-dimension').prop('disabled', true);
      }
    });
  }

  function changeTemplateSize(template, backsideTemplate) {
    var tpl = $('.template-container');
    var templateWidth = parseFloat($('.template-width').val());
    var templateHeight = parseFloat($('.template-height').val());

    tpl.width(Math.round(templateWidth * pixelsPerCm));
    tpl.height(Math.round(templateHeight * pixelsPerCm));
    previousTemplateDimensions.width = templateDimensions.width;
    previousTemplateDimensions.height = templateDimensions.height;
    templateDimensions = new Dimensions(
      Math.round(templateWidth * DEFAULT_PIXEL_CM),
      Math.round(templateHeight * DEFAULT_PIXEL_CM)
    );
    updateRulers();
    displayAllBackgrounds(template, backsideTemplate);
    updatePreset(templateWidth, templateHeight);
  }

  function moveSelectedItem(direction) {
    var selectedItem = getSelectedItemData();
    var div = $('.designer-item.selected').parent();
    ({
      left: function() {
        if (div) {
          div.css('left', 0);
          selectedItem.x = 0;
        }
      },
      right: function() {
        if (div) {
          var x = templateDimensions.width - div.width();
          div.css('left', x > 0 ? x + 'px' : 0);
          selectedItem.x = unzoom(x > 0 ? x : 0);
        }
      },
      center: function() {
        if (div) {
          var x = (templateDimensions.width - div.width()) / 2;
          var y = (templateDimensions.height - div.height()) / 2;
          div.css('left', x > 0 ? x + 'px' : 0);
          div.css('top', y > 0 ? y + 'px' : 0);
          selectedItem.x = unzoom(x > 0 ? x : 0);
          selectedItem.y = unzoom(y > 0 ? y : 0);
        }
      },
      top: function() {
        if (div) {
          div.css('top', 0);
          selectedItem.y = 0;
        }
      },
      bottom: function() {
        if (div) {
          var y = templateDimensions.height - div.height();
          div.css('top', y > 0 ? y + 'px' : 0);
          selectedItem.y = unzoom(y > 0 ? y : 0);
        }
      },
      back: function() {
        if (div) {
          const backmostItem = _.minBy(
            Object.values(items).filter(
              item => selectedItem.id !== item.id && itemsOverlap(selectedItem, item)
            ),
            'zIndex'
          );
          const zIndex = Math.min(selectedItem.zIndex, backmostItem.zIndex - 1);
          selectedItem.zIndex = zIndex;
          normalizeZIndex();
        }
      },
      front: function() {
        if (div) {
          const foremostItem = _.maxBy(
            Object.values(items).filter(
              item => selectedItem.id !== item.id && itemsOverlap(selectedItem, item)
            ),
            'zIndex'
          );
          const zIndex = Math.max(selectedItem.zIndex, foremostItem.zIndex + 1);
          selectedItem.zIndex = zIndex;
          normalizeZIndex();
        }
      },
    }[direction]());
  }

  function itemsOverlap(item1, item2) {
    const {x: left1, y: top1} = item1;
    const {x: left2, y: top2} = item2;

    const right1 = left1 + item1.width;
    const bottom1 = top1 + (item1.height || 22);
    const right2 = left2 + item2.width;
    const bottom2 = top2 + (item2.height || 22);

    if (left1 >= right2 || left2 >= right1) {
      return false;
    }
    return !(top1 >= bottom2 || top2 >= bottom1);
  }

  function normalizeZIndex() {
    _.sortBy(Object.values(items), 'zIndex').forEach((item, n) => {
      item.zIndex = n + 10;
      $('.ui-draggable[data-id=' + item.id + ']').css('zIndex', n + 10);
    });
  }

  function setSelectedItemAttribute(attribute) {
    var selectedItem = getSelectedItemData();
    var div = $('.designer-item.selected');

    if (!div) {
      return;
    }

    ({
      font: function() {
        selectedItem.font_family = $('#font-selector').val();
      },
      color: function() {
        selectedItem.color = $('#text-color-selector').val();
      },
      background_color: function() {
        selectedItem.background_color = $('#bg-color-selector').val();
      },
      alignment: function() {
        selectedItem.text_align = $('#alignment-selector').val();
      },
      size: function() {
        selectedItem.font_size = $('#size-selector').val();
      },
      style: function() {
        switch ($('#style-selector').val()) {
          case 'normal':
            selectedItem.bold = false;
            selectedItem.italic = false;
            break;
          case 'bold':
            selectedItem.bold = true;
            selectedItem.italic = false;
            break;
          case 'italic':
            selectedItem.bold = false;
            selectedItem.italic = true;
            break;
          case 'bold_italic':
            selectedItem.bold = true;
            selectedItem.italic = true;
            break;
        }
      },
      text: function() {
        var $fixedTextField = $('#fixed-text-field');
        selectedItem.text = unescapeHTML($fixedTextField.val());
        $fixedTextField.val(selectedItem.text);
      },
      width: function() {
        selectedItem.width = Math.round($('.js-element-width').val() * pixelsPerCm);
        if (selectedItem.type === 'ticket_qr_code') {
          $('.js-element-height').val($('.js-element-width').val());
          selectedItem.height = selectedItem.width;
        }
      },
      height: function() {
        selectedItem.height = Math.round($('.js-element-height').val() * pixelsPerCm);
        if (selectedItem.type === 'ticket_qr_code') {
          $('.js-element-width').val($('.js-element-height').val());
          selectedItem.width = selectedItem.height;
        }
      },
    }[attribute]());

    div.replaceWith(selectedItem.toHTML());
    if (selectedItem.type === 'fixed_image') {
      $('.designer-item.selected').append(createFixedImageElement(selectedItem));
    }
  }

  function save(template) {
    if ($('.js-template-name').val() === '') {
      alertPopup($T.gettext('Please choose a name for the template'), $T('Warning'));
      return;
    }
    if (!Object.keys(items).length && !template.background_url) {
      alertPopup(
        $T.gettext('The template cannot be empty. Add some elements or a background image.'),
        $T.gettext('Warning')
      );
      return;
    }
    if (Object.values(items).some(item => item.type === 'fixed_image' && !item.image_id)) {
      alertPopup(
        $T.gettext(
          'The Fixed image element cannot be empty. Upload an image inside it or remove it.'
        ),
        $T.gettext('Warning')
      );
      return;
    }
    if (removeBackSide) {
      backsideTemplateID = null;
    }
    var templateData = {
      template: {
        width: templateDimensions.realWidth,
        height: templateDimensions.realHeight,
        background_position: $('input[name=bg-position]:checked').val(),
        items: _.values(items).map(function(item) {
          var itemCopy = $.extend(true, {}, item);
          itemCopy.font_size = unzoomFont(item.font_size);
          return item;
        }),
      },
      clear_background: !template.background_url,
      title: $('.js-template-name').val(),
      is_clonable: $('input[name="is-clonable"]:checked').length > 0,
      backside_template_id: backsideTemplateID,
    };

    var confirmed = showConfirmationDialog
      ? confirmPrompt(
          $T.gettext('Are you sure you want to change the dimensions of this template?') +
            confirmMessage,
          confirmTitle
        )
      : $.Deferred().resolve();

    confirmed.then(function() {
      $.ajax({
        url: location.pathname,
        data: JSON.stringify(templateData),
        contentType: 'application/json',
        method: 'POST',
        complete: IndicoUI.Dialogs.Util.progress(),
        error: handleAjaxError,
        success: function(data) {
          initialWidth = templateDimensions.width;
          initialHeight = templateDimensions.height;
          if (removeBackSide) {
            $('.affected-targets-warning').hide('fast');
            togglePlaceholderToBeRemoved(false);
            $('.js-remove-backside').click();
            removeBackSide = false;
            showConfirmationDialog = false;
          }
          handleFlashes(data, true);
        },
      });
    });
  }

  function setBackgroundPos($background, mode) {
    if (mode === 'stretch') {
      $background.css({
        left: 0,
        top: 0,
      });
      $background.height(templateDimensions.height);
      $background.width(templateDimensions.width);
    } else if (mode === 'center') {
      var imgDimensions = getImageRealDimensions($background);
      var ratio;
      $background.height(imgDimensions.height);
      $background.width(imgDimensions.width);

      if (
        $background.width() > templateDimensions.width ||
        $background.height() > templateDimensions.height
      ) {
        if ($background.width() > templateDimensions.width) {
          ratio = templateDimensions.width / $background.width();

          $background.width(templateDimensions.width);
          $background.height($background.height() * ratio);
          $background.css({
            left: 0,
            top: templateDimensions.height / 2.0 - $background.height() / 2.0 + 'px',
          });
        }

        if ($background.height() > templateDimensions.height) {
          ratio = templateDimensions.height / $background.height();

          $background.width($background.width() * ratio);
          $background.height(templateDimensions.height);

          $background.css({
            left: templateDimensions.width / 2.0 - $background.width() / 2.0 + 'px',
            top: 0,
          });
        }
      } else {
        $background.css({
          left: templateDimensions.width / 2 - imgDimensions.width / 2 + 'px',
          top: templateDimensions.height / 2 - imgDimensions.height / 2 + 'px',
        });
      }
    }
  }

  function displayBackground(template, isBackside) {
    var templateSideClass = isBackside ? '.template-side.back' : '.template-side.front';
    var $backgroundElement = $(templateSideClass).find('.background-image');
    var backgroundPos = template.data.background_position;

    $backgroundElement
      .attr({
        src: template.background_url,
      })
      .css({
        position: 'absolute',
        left: 0,
        top: 0,
        height: templateDimensions.height + 'px',
        width: templateDimensions.width + 'px',
        zIndex: 5,
      })
      .on('load', function() {
        $('#loadingIcon').hide();
        setBackgroundPos($(this), backgroundPos);
      })
      .appendTo(templateSideClass);
  }

  function displayAllBackgrounds(template, backsideTemplate) {
    displayBackground(template);
    if (backsideTemplate.background_url) {
      displayBackground(backsideTemplate, true);
    }
  }

  function removeBackground(template) {
    if (template.background_url) {
      template.background_url = null;
      $('.template-side.front').trigger('indico:backgroundChanged');
    }
  }

  function createFixedImageElement(item) {
    const $imageElement = $('<img/>');
    $imageElement
      .attr({
        src: images[item.image_id],
      })
      .css({
        position: 'absolute',
        left: 0,
        top: 0,
        height: item.height + 'px',
        width: item.width + 'px',
      });
    return $imageElement;
  }

  function displayFixedImage() {
    const $div = $('.ui-draggable[data-id=' + lastSelectedItem.id + '] div');
    $div.text('');
    $div.find('img').remove();
    const $imageElement = createFixedImageElement(lastSelectedItem);
    $imageElement.appendTo($div);
    const $imageFile = $('#imageFile');
    $imageFile.val('');
    $imageFile
      .next('label')
      .addClass('i-button')
      .text($T.gettext('Choose a file'));
    $('.js-upload-img').prop('disabled', $imageFile.val());
    $('.js-remove-img').prop('disabled', !lastSelectedItem.image_id);
  }

  function removeFixedImage(item) {
    if (item.image_id) {
      item.image_id = null;
      $('.ui-draggable[data-id=' + item.id + '] div').text($T.gettext('Fixed Image'));
      $('.ui-draggable[data-id=' + item.id + '] img').remove();
      $('.js-remove-img').prop('disabled', !item.image_id);
    }
  }

  function unescapeHTML(str) {
    // taken from Prototype
    return str
      .replace(/<\w+(\s+("[^"]*"|'[^']*'|[^>])+)?>|<\/\w+>/gi, '')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&amp;/g, '&');
  }

  function displayTemplate(template, isBackside) {
    if (template.data) {
      template.data.items.forEach(function(item) {
        createItemFromObject(item, isBackside);
      });
      displayItems(isBackside);
    }

    var hasBackside =
      isBackside && template.data && (template.data.items.length || template.background_url);
    toggleBacksidePlaceholder(!hasBackside);

    if (template.background_url) {
      displayBackground(template, isBackside);
    }
  }

  function clearBacksideTemplate(template) {
    var $templateSide = $('.template-side.back');
    if (template.background_url) {
      template.background_url = null;
      $templateSide.find('.background-image').remove();
      $templateSide.append($('<img>', {class: 'background-image'}));
    }
    $templateSide.find('.designer-item').remove();
    template.title = null;
    template.data = null;
    backsideItems = {};
  }

  function toggleBacksidePlaceholder(showPlaceholder) {
    var $placeholder = $('.backside-placeholder');

    $placeholder.parent().toggleClass('empty', showPlaceholder);
    $placeholder.toggle(showPlaceholder);
    $('.backside-tools').toggleClass('hidden', showPlaceholder);
  }

  function togglePlaceholderToBeRemoved(showPlaceholder) {
    toggleBacksidePlaceholder(showPlaceholder);
    $('.backside-tools').toggleClass('hidden', !showPlaceholder);
    if (showPlaceholder) {
      $('.backside-placeholder').addClass('to-be-removed');
      $('.placeholder-text').html($T.gettext('This back side template will be removed'));
      $('.placeholder-link').hide();
      confirmMessage = $T.gettext('The back side of this template will be removed');
      confirmTitle = $T.gettext('Disassociate back side');
      removeBackSide = true;
    } else {
      $('.backside-placeholder').removeClass('to-be-removed');
      $('.placeholder-text').html($T.gettext('The back side is empty.'));
      $('.placeholder-link').show();
      confirmMessage = $T.gettext(
        'The back side of the templates that use this one as the back side will be removed.'
      );
      confirmTitle = $T.gettext('Disassociate back sides');
      removeBackSide = false;
    }
  }

  function toggleWarningOnDimensionChange(
    xDimension,
    yDimension,
    initialXDimension,
    initialYDimension
  ) {
    if (!$('#backside-warning').length && backsideTemplateID === null) {
      return;
    }
    var $backsideTplsWarning = null;
    if ($('#backside-warning').length && backsideTemplateID !== null) {
      $backsideTplsWarning = $('.affected-targets-warning');
    } else if ($('#backside-warning').length) {
      $backsideTplsWarning = $('#backside-warning');
    } else if (backsideTemplateID !== null) {
      $backsideTplsWarning = $('#frontside-warning');
    }
    if (xDimension.val() * DEFAULT_PIXEL_CM !== initialXDimension) {
      if (backsideTemplateID !== null) {
        togglePlaceholderToBeRemoved(true);
      }
      $backsideTplsWarning.show('fast');
      showConfirmationDialog = true;
    } else if (yDimension.val() * DEFAULT_PIXEL_CM === initialYDimension) {
      $backsideTplsWarning.hide('fast');
      if (backsideTemplateID !== null) {
        togglePlaceholderToBeRemoved(false);
      }
      showConfirmationDialog = false;
    }
  }

  function removeWarning() {
    $('#frontside-warning').hide('fast');
    togglePlaceholderToBeRemoved(false);
    removeBackSide = false;
    showConfirmationDialog = false;
  }

  global.setupDesigner = function setupDesigner(
    template,
    backsideTemplate,
    config,
    placeholders,
    imageTypes_
  ) {
    editing = !!template;
    itemTitles = Object.assign(...Object.values(placeholders).map(({options}) => options));

    zoomFactor = config.zoom_factor;
    // Number of pixels per cm
    pixelsPerCm = zoom(DEFAULT_PIXEL_CM);

    // Number of pixels, both horizontal and vertical, that are between the top left corner
    // and the position where items are inserted
    initialOffset = pixelsPerCm;

    backsideTemplateID = backsideTemplate.id;

    imageTypes = imageTypes_;

    images = {...template.images, ...backsideTemplate.images};

    // Item class
    $(document).ready(function() {
      var removeBackgroundQtip = $('.js-remove-bg').qtip();

      $('#bg-form input[type="file"]').on('change', function() {
        var $this = $(this);
        if (this.files) {
          $this
            .next('label')
            .removeClass('i-button')
            .text(this.files[0].name);
        }
        $('.js-upload-bg')
          .prop('disabled', !$this.val())
          .toggleClass('highlight', !!$this.val());
      });

      $('#img-form input[type="file"]').on('change', function() {
        var $this = $(this);
        if (this.files) {
          $this
            .next('label')
            .removeClass('i-button')
            .text(this.files[0].name);
        }
        $('.js-upload-img')
          .prop('disabled', !$this.val())
          .toggleClass('highlight', !!$this.val());
      });

      // select and inline edit
      $('.template-content')
        .on('mousedown', '.designer-item', function() {
          selectItem($(this));
        })
        .on('dblclick', '.designer-item', function() {
          inlineEditItem($(this));
        });

      $('.js-upload-bg').click(function() {
        $('.js-toggle-side.front').click();
        $('#bg-form').submit();
        return false;
      });

      $('.js-upload-img').click(function() {
        lastSelectedItem = getSelectedItemData();
        if (lastSelectedItem.type === 'fixed_image') {
          $('#img-form').submit();
        }
        return false;
      });

      // toggle grid/snap mode
      $('#grid-snap')
        .change(function() {
          snapToGrid = this.checked;
        })
        .change();

      $('#bg-form').ajaxForm({
        dataType: 'json',
        iframe: false,
        success: function(data) {
          if (data.error) {
            alertPopup(data.error, $T('Error'));
            return;
          }
          template.background_url = data.image_url;
          displayBackground(template);
          $('.template-side.front').trigger('indico:backgroundChanged');
        },
      });

      $('#img-form').ajaxForm({
        dataType: 'json',
        iframe: false,
        success: function(data) {
          if (data.error) {
            alertPopup(data.error, $T('Error'));
            return;
          }
          if (lastSelectedItem.type === 'fixed_image') {
            lastSelectedItem.image_id = data.image_id;
            images[data.image_id] = data.image_url;
            displayFixedImage();
          }
        },
      });

      $('input[name=bg-position]').change(function(e) {
        e.preventDefault();
        var newPosition = $(this).val();
        var $backgroundElement = $('.template-side.front .background-image');

        setBackgroundPos($backgroundElement, newPosition);
        template.data.background_position = newPosition;
      });

      $('.js-remove-bg').click(function(e) {
        e.preventDefault();
        removeBackgroundQtip.qtip('api').toggle();
        removeBackground(template);
      });

      $('.js-remove-img').click(function(e) {
        e.preventDefault();
        const selectedItem = getSelectedItemData();
        if (selectedItem.type === 'fixed_image') {
          removeFixedImage(selectedItem);
        }
      });

      $('.move-button').click(function(e) {
        e.preventDefault();
        var direction = $(this).data('direction');
        moveSelectedItem(direction);
      });

      $('.js-font-tool').change(function() {
        var attr = $(this).data('attr');
        setSelectedItemAttribute(attr, config);
      });

      $('.insert-element-btn').click(function(e) {
        e.preventDefault();
        $('.js-toggle-side.front').click();
        insertElement();
      });

      $('.js-remove-element').click(function(e) {
        e.preventDefault();
        removeSelectedElement();
      });

      $('.js-save-template').click(function(e) {
        e.preventDefault();
        save(template);
      });

      $('.template-width, .template-height').on('input', function() {
        changeTemplateSize(template, backsideTemplate);
      });

      $('.js-element-width').on('keyup click', function() {
        setSelectedItemAttribute('width', config);
      });

      $('.js-element-height').on('keyup click', function() {
        setSelectedItemAttribute('height', config);
      });

      $('#fixed-text-field').on('keyup', function() {
        setSelectedItemAttribute('text', config);
      });

      $('.js-preset-tool').on('change', function() {
        var $selectedOption = $(this).find('option:selected');

        if ($selectedOption.val() !== 'custom') {
          $('.template-width')
            .val($selectedOption.data('width'))
            .change();
          $('.template-height')
            .val($selectedOption.data('height'))
            .change();
          changeTemplateSize(template, backsideTemplate);
        }
        $('.js-template-dimension').prop('disabled', $selectedOption.val() !== 'custom');
      });

      $('.js-toggle-side').on('click', function() {
        var $this = $(this);
        var newFaceUp = $this.hasClass('front') ? 'front' : 'back';
        var $selectedItem = $('.designer-item.selected');
        var hasBackside =
          backsideTemplate.data &&
          (backsideTemplate.data.items.length || backsideTemplate.background_url);

        $('.template-content').toggleClass('flipped', newFaceUp === 'back');
        $('.template-side.back').toggleClass('active', newFaceUp === 'back');
        $('.template-side.front').toggleClass('active', newFaceUp === 'front');
        $('.backside-tools').toggleClass('hidden', newFaceUp === 'front' || !hasBackside);
        $('.js-toggle-side').removeClass('highlight');
        $('.element-tools').addClass('hidden');
        $('.js-hide-on-flip').toggle(newFaceUp !== 'back');
        $('.js-invisible-on-flip').toggleClass('disappear', newFaceUp === 'back');
        $this.toggleClass('highlight');
        if ($selectedItem && $selectedItem[0]) {
          deselectItem($selectedItem);
        }
        $('.template-side.active').trigger('indico:backgroundChanged');
      });

      $('.template-side').on('indico:backgroundChanged', function() {
        var $backgroundFile = $('#backgroundFile');
        var $templateSide = $('.template-side.front');
        var $templateSideBackground = $templateSide.find('.background-image');

        if (!template.background_url && $templateSideBackground.attr('src')) {
          $templateSideBackground.remove();
          $templateSide.append($('<img>', {class: 'background'}));
          $backgroundFile.val('');
          $backgroundFile
            .next('label')
            .addClass('i-button')
            .text($T.gettext('Choose a file'));
        }
        $('.js-upload-bg').prop('disabled', !$backgroundFile.val());
        $('.js-remove-bg').prop('disabled', !template.background_url);
        $('#bg-position-stretch').prop('checked', template.data.background_position === 'stretch');
        $('#bg-position-center').prop('checked', template.data.background_position === 'center');
      });

      $('.template-side.front').trigger('indico:backgroundChanged');

      $('.template-side.back').on('indico:backsideUpdated', function(evt, data) {
        backsideTemplateID = data.backside_template_id;
        Object.assign(images, data.template.images);
        clearBacksideTemplate(backsideTemplate);
        displayTemplate(data.template, true);
        backsideTemplate = data.template;
        if (removeBackSide) {
          removeWarning();
        }
        $('.backside-template-title, .js-front-affected-title').text(data.template.title);
      });

      $('.js-remove-backside').on('click', function() {
        backsideTemplateID = null;
        clearBacksideTemplate(backsideTemplate);
        if (removeBackSide) {
          removeWarning();
        }
        toggleBacksidePlaceholder(true);
      });

      $('.js-change-orientation').on('click', function() {
        var $width = $('.template-width');
        var $height = $('.template-height');
        var widthValue = $width.val();

        $width.val($height.val()).change();
        $height.val(widthValue).change();
        changeTemplateSize(template, backsideTemplate);
      });

      $('.js-backside-list-dialog').on('click', function() {
        var $this = $(this);

        ajaxDialog({
          trigger: $this,
          url: $this.data('href'),
          data: {
            width: templateDimensions.realWidth,
            height: templateDimensions.realHeight,
          },
          title: $this.data('title'),
        });
      });

      $('.backside-tools').addClass('hidden');

      var $templateWidth = $('.template-width');
      var $templateHeight = $('.template-height');
      $templateWidth.on('change input', function() {
        toggleWarningOnDimensionChange($(this), $templateHeight, initialWidth, initialHeight);
      });
      $templateHeight.on('change input', function() {
        toggleWarningOnDimensionChange($(this), $templateWidth, initialHeight, initialWidth);
      });

      $('.js-back-affected').qbubble({
        overwrite: true,
        position: {
          target: $('.js-back-affected'),
        },
        content: {
          text: $('.back-warning-qtip-content').html(),
        },
        hide: {
          event: 'unfocus click',
        },
        show: {
          event: 'click',
        },
      });

      $('.js-front-affected').qbubble({
        overwrite: true,
        position: {
          target: $('.js-front-affected'),
        },
        content: {
          text: function() {
            return $('.front-warning-qtip-content').html();
          },
        },
        hide: {
          event: 'unfocus click',
        },
        show: {
          event: 'click',
        },
      });
    });

    // We load the template if we are editing a template
    if (editing) {
      // We give the toHTML() method to each of the items
      templateDimensions = new Dimensions(template.data.width, template.data.height);
      $('.js-template-name').val(template.title);
      $('.js-is-clonable').prop('checked', template.is_clonable);
      $('.template-container')
        .width(templateDimensions.width)
        .height(templateDimensions.height);
    } else {
      templateDimensions = new Dimensions(config.tpl_size[0], config.tpl_size[1]);
    }

    previousTemplateDimensions = new Dimensions(0, 0);

    $('.template-width').val(templateDimensions.width / pixelsPerCm);
    $('.template-height').val(templateDimensions.height / pixelsPerCm);

    initialWidth = templateDimensions.width;
    initialHeight = templateDimensions.height;

    updateRulers(); // creates the initial rulers
    changeTemplateSize(template, backsideTemplate);
    displayTemplate(template);
    displayTemplate(backsideTemplate, true);
  };
})(window);
