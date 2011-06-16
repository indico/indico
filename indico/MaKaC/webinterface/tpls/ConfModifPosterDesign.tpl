<script type="text/javascript">
    var snapToGrid = false;

    // "Zoom factor" - the size of the document, related to reality
    var zoom_factor = 0.5

    // Dimensions of the template space, in pixels
    var templateDimensions;

    // Previous dimensions of the template space, in cm
    var previousTemplateDimensions;

    // Number of pixels per cm
    var pixelsPerCm = 50 * zoom_factor;

    // Id and position of the background used
    var backgroundId = -1
    var backgroundPos;

    // Number of pixels, both horizontal and vertical, that are between the top left corner
    // and the position where items are inserted
    var initialOffset = pixelsPerCm;

    // Id of the next element to be inserted
    var itemId = -1;

    // Common parts of many elements
    var elementCommon1 = '<table border="2" cellpadding="0" cellspacing="0" style="cursor:move;" width="200"><tbody><tr><td align="center">';
    var elementCommon2 = '</td></tr></tbody></table>';

    // Last selected item (holds the div for that item)
    var lastSelectedDiv = null;

    // Translation dictionary from key to name in current language.
    var translate = ${translateName};

    // List of poster template items
    var items = [];

    var firstLoad = true;

    // Item class
    function Item(itemId, key) {
        this.id = itemId;
        this.key = key;
        this.x = initialOffset;
        this.y = initialOffset;
        this.fontFamily = "Times New Roman";
        this.bold = false;
        this.italic = false;
        this.textAlign = "Center";
        this.color = "black";
        this.fontSize = "25pt";
        this.width = 400;
        this.text = "(Type your text)" // Only for fixed text items

        // The following attributes have no meaning to the server
        this.selected = false;
        this.fontFamilyIndex = 0;
        this.styleIndex = 0;
        this.textAlignIndex = 2; //Center
        this.colorIndex = 0;
        this.fontSizeIndex = 11; //Medium
    }

    Item.prototype.toHTML = function () {
        return '<table border="2" cellpadding="0" cellspacing="0"' +
               ' width="' + this.width + '" bgcolor="' + (this.selected ? "#CCCCFF" : "white") +
               '" style="cursor:move; font-weight:' + (this.bold ? 'bold' : 'normal') + '; font-style:' + (this.italic ? 'italic' : 'normal') +
               '; text-align: ' + this.textAlign.replace('Justified', 'justify') + ';"' +
               '><tbody><tr><td><span style="color:' + this.color + '; font-family: ' + this.fontFamily + '; font-size:' + this.fontSize + ';">' +
               (this.key == "Fixed Text" ? this.text : translate[this.key]) +
               '</span></td></tr></tbody></table>';
    }

    // Dimensions class
    function Dimensions(width, height) {
        this.width = width
        this.height = height
    }

    // This function creates a new draggable div
    function createDiv() {
        // Each div has:
        // -an unique id, which is a natural number (0, 1, 2, ...)
        // -a type (stored in the name attribute)
        // -absolute x,y position
        // -an inner HTML with its content
        itemId++;

        var newDiv = $j('<div/>', {
            id: itemId
        }).css({
            position: 'absolute',
            left: initialOffset + 'px',
            top: initialOffset + 'px',
            zIndex: itemId + 10
        }).appendTo('#templateDiv');

        newDiv.draggable({
            containment: '#templateDiv',
            stack: '#templateDiv > div',
            opacity: 0.5,
            drag: function(e, ui) {
                if (snapToGrid) {
                    ui.position.left = Math.floor(ui.position.left / 10) * 10;
                    ui.position.top = Math.floor(ui.position.top / 10) * 10;
                }
            },
            stop: function(e, ui) {
                items[this.id].x = ui.position.left;
                items[this.id].y = ui.position.top;
            }
        });

        return newDiv;
    }

    // This function inserts the selected element in the blank space where poster template designing takes place
    function insertElement() {
        var newDiv = createDiv();
        // We set the inner html of the div depending on the type of item inserted
        switch($j('#elementList').val()) {
            ${ switchCases }
        }

        if (!lastSelectedDiv) {
            markSelected(newDiv);
        }

        initialOffset += 10;
    }

    function removeElement() {
        if (lastSelectedDiv) {
            items[lastSelectedDiv.attr('id')] = false;
            lastSelectedDiv.remove();
            $j('#selection_text').html('');
            lastSelectedDiv = null;
            $j('#removeButton').prop('disabled', true);
        }
    }

    function markSelected(newSelectedDiv) {
        // Change the text that says which item is selected
        var id = newSelectedDiv.attr('id');
        $j('#selection_text').html(translate[items[id].key]);

        // TODO: add check to see if there's a table inside and not an image

        // Change the background color of the old selected item and the new selected item
        if (lastSelectedDiv) {
            var lastId = lastSelectedDiv.attr('id');
            items[lastId].selected = false;
            lastSelectedDiv.html(items[lastId].toHTML());
        }

        var newSelectedItem = items[id];
        newSelectedItem.selected = true;
        newSelectedDiv.html(newSelectedItem.toHTML());
        lastSelectedDiv = newSelectedDiv;
        $j('#removeButton').prop('disabled', false);

        // Change the selectors so that they match the properties of the item
        $j('#alignment_selector').prop('selectedIndex', newSelectedItem.textAlignIndex);
        $j('#font_selector').prop('selectedIndex', newSelectedItem.fontFamilyIndex);
        $j('#size_selector').prop('selectedIndex', newSelectedItem.fontSizeIndex);
        $j('#style_selector').prop('selectedIndex', newSelectedItem.styleIndex);
        $j('#color_selector').prop('selectedIndex', newSelectedItem.colorIndex);
        $j('#width_field').val(newSelectedItem.width / pixelsPerCm);
        if (newSelectedItem.key == "Fixed Text") {
            $j('#fixed_text_field').val(newSelectedItem.text).prop('disabled', false);
            $j('#changeText').prop('disabled', false);
        } else {
            $j('#fixed_text_field').val("").prop('disabled', true);
            $j('#changeText').prop('disabled', true);
        }
    }

    function updateRulers() {
        if (templateDimensions.width > previousTemplateDimensions.width) {
            var hRuler = $j('#horizontal_ruler');
            for (var i = Math.ceil(previousTemplateDimensions.width / pixelsPerCm); i < Math.ceil(templateDimensions.width / pixelsPerCm); i++) {
                $j('<div/>', {
                    id: 'rulerh' + i
                }).css({
                    width: pixelsPerCm - 1 + 'px',
                    height: '10px',
                    position: 'absolute',
                    border: '1px solid black',
                    borderTop: 'none',
                    background: '#eee',
                    textAlign: 'right',
                    fontSize: '6pt',
                    left: (i * pixelsPerCm - 1) + 'px',
                    top: 0
                }).html(i + 1).appendTo(hRuler);
            }
        }
        else if (templateDimensions.width < previousTemplateDimensions.width) {
            for (var i = Math.ceil(previousTemplateDimensions.width / pixelsPerCm); i > Math.ceil(templateDimensions.width / pixelsPerCm); i--) {
                $j('#horizontal_ruler > #rulerh' + (i - 1)).remove();
            }
        }

        if (templateDimensions.height > previousTemplateDimensions.height) {
            var vRuler = $j('#vertical_ruler');
            for (var i = Math.ceil(previousTemplateDimensions.height / pixelsPerCm); i < Math.ceil(templateDimensions.height / pixelsPerCm); i++) {
                $j('<div/>', {
                    id: 'rulerv' + i
                }).css({
                    width: '10px',
                    height: pixelsPerCm - 1 + 'px',
                    position: 'absolute',
                    border: '1px solid black',
                    borderLeft: 'none',
                    background: '#eee',
                    verticalAlign: 'bottom',
                    fontSize: '6pt',
                    left: 0,
                    top: (i * pixelsPerCm - 1) + 'px'
                }).html('<p style="font-size: 6pt; margin-bottom: 0px;">' + (i + 1) + '</p>').appendTo(vRuler);
            }
        }
        else if (templateDimensions.height < previousTemplateDimensions.height) {
            for (i = Math.ceil(previousTemplateDimensions.height / pixelsPerCm); i > Math.ceil(templateDimensions.height / pixelsPerCm); i--) {
                $j('#vertical_ruler > #rulerv' + (i - 1)).remove();
            }
        }
    }

    // This function displays all the items in the 'items' array on the screen
    // If there are already some items being displayed, it does not erase them
    function displayItems() {
        $j.each(items, function(i, item) {
            var newDiv = createDiv();
            newDiv.css({
                left: item.x + 'px',
                top: item.y + 'px'
            });
            item.fontSize = zoom_font(zoom_factor, item.fontSize);
            newDiv.html(item.toHTML());
            if (item.selected) {
                markSelected(newDiv);
            }
        });
    }


    function changeTemplateSize() {
        var tpl = $j('#templateDiv');
        tpl.width($j('#poster_width').val() * pixelsPerCm);
        tpl.height($j('#poster_height').val() * pixelsPerCm);
        previousTemplateDimensions.width = templateDimensions.width;
        previousTemplateDimensions.height = templateDimensions.height;
        templateDimensions = new Dimensions($j('#poster_width').val() * pixelsPerCm, $j('#poster_height').val() * pixelsPerCm);
        updateRulers();
        if (backgroundId != -1) {
            var url = $j('#background').attr('src');
            $j('#background').remove();
            displayBackground(url);
        }
    }

    var moveFuncs = {
        left: function() {
            if (lastSelectedDiv) {
                lastSelectedDiv.css('left', 0);
                items[lastSelectedDiv.attr('id')].x = 0 + "px";
            }
        },
        right: function() {
            if (lastSelectedDiv) {
                lastSelectedDiv.css('left', (templateDimensions.width - lastSelectedDiv.width() - 1) + "px"); // -1 because of the table border
                items[lastSelectedDiv.attr('id')].x = (templateDimensions.width - lastSelectedDiv.width() - 1) + "px";
            }
        },
        center: function() {
            if (lastSelectedDiv) {
                lastSelectedDiv.css('left', ((templateDimensions.width - lastSelectedDiv.width() - 1) / 2) + "px");
                lastSelectedDiv.css('top', ((templateDimensions.height - lastSelectedDiv.height() - 1) / 2) + "px");
                items[lastSelectedDiv.attr('id')].x = ((templateDimensions.width - lastSelectedDiv.width() - 1) / 2) + "px";
                items[lastSelectedDiv.attr('id')].y = ((templateDimensions.height - lastSelectedDiv.height() - 1) / 2) + "px";
            }
        },
        top: function() {
            if (lastSelectedDiv) {
                lastSelectedDiv.css('top', 0);
                items[lastSelectedDiv.attr('id')].y = 0 + "px";
            }
        },
        bottom: function() {
            if (lastSelectedDiv) {
                lastSelectedDiv.css('top', (templateDimensions.height - lastSelectedDiv.height() - 1) + "px");
                items[lastSelectedDiv.attr('id')].y = (templateDimensions.height - lastSelectedDiv.height() - 1) + "px";
            }
        }
    };

    var attrFuncs = {
        font: function() {
            if (lastSelectedDiv) {
                var item = items[lastSelectedDiv.attr('id')];
                item.fontFamily = $j('#font_selector').val();
                item.fontFamilyIndex = $j('#font_selector').prop('selectedIndex');
                lastSelectedDiv.html(item.toHTML());
            }
        },
        color: function() {
            if (lastSelectedDiv) {
                var item = items[lastSelectedDiv.attr('id')];
                item.color = $j('#color_selector').val();
                item.colorIndex = $j('#color_selector').prop('selectedIndex');
                lastSelectedDiv.html(item.toHTML());
            }
        },
        alignment: function() {
            if (lastSelectedDiv) {
                var item = items[lastSelectedDiv.attr('id')];
                item.textAlign = $j('#alignment_selector').val();
                item.textAlignIndex = $j('#alignment_selector').prop('selectedIndex');
                lastSelectedDiv.html(item.toHTML());
            }
        },
        size: function() {
            if (lastSelectedDiv) {
                var item = items[lastSelectedDiv.attr('id')];
                item.fontSize = zoom_font(zoom_factor, $j('#size_selector').val());
                item.fontSizeIndex = $j('#size_selector').prop('selectedIndex');
                lastSelectedDiv.html(item.toHTML());
            }
        },
        style: function() {
            if (lastSelectedDiv) {
                var item = items[lastSelectedDiv.attr('id')];
                switch($j('#style_selector').val()) {
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

                item.styleIndex = $j('#style_selector').prop('selectedIndex');
                lastSelectedDiv.html(item.toHTML());
            }
        },
        text: function() {
            if (lastSelectedDiv) {
                var item = items[lastSelectedDiv.attr('id')];
                item.text = unescapeHTML($j('#fixed_text_field').val());
                $j('#fixed_text_field').val(item.text);
                lastSelectedDiv.html(item.toHTML());
            }
        },
        width: function() {
            if (lastSelectedDiv) {
                var item = items[lastSelectedDiv.attr('id')];
                item.width = $j('#width_field').val() * pixelsPerCm;
                lastSelectedDiv.html(item.toHTML());
            }
        }
    };

    function zoom_font(zfact, fontSize) {
        var pattern = /([0-9.]+)pt/g
        var ftsize = pattern.exec(fontSize)[1];
        return (ftsize * zfact) + 'pt';
    }

    function save() {
        if ($j('#template_name').val() == '') {
            alert("Please choose a name for the template");
            return;
        }
        var template = [];
        template.push($j('#template_name').val());
        template.push(templateDimensions, pixelsPerCm);
        template.push(backgroundId);

        $j.each(items, function(i, item) {
            if (item != false) {
                item.fontSize = zoom_font(1/zoom_factor, item.fontSize);
            }
        });

        template.push(items);
        $j('#templateData').val(Json.write(template));
        $j('#saveForm').submit();
    }

    function sent() {
        if (firstLoad) {
            firstLoad = false;
        }
        else {
            var iframeDocument = $j('#uploadTarget')[0].contentDocument || $j('#uploadTarget')[0].contentWindow;
            if (iframeDocument.document) {
                iframeDocument = iframeDocument.document;
            }

            try {
                if (backgroundId != -1) {
                    $j('#background').remove();
                }
                backgroundId = $j('#background_id', iframeDocument).html();
                var backgroundURL = $j('#background_url', iframeDocument).html();
                backgroundPos = $j('#background_pos', iframeDocument).html();
                displayBackground(backgroundURL);
            }
            catch (err) {
                $j('#loadingIcon').hide();
            }
        }
    }

    function setBackgroundPos(mode) {
        var background = $j('#background');
        var hiddenField = $j('#bgPosition');
        var bgPosStretch = $j('#bgPosStretch');
        var bgPosCenter = $j('#bgPosCenter');

        if (mode == 'Stretch') {
            background.css({
                left: 0,
                top: 0
            });
            background.height(templateDimensions.height);
            background.width(templateDimensions.width);
            bgPosStretch.prop('checked', true);
            bgPosCenter.prop('checked', false);
        }
        else if (mode == 'Center') {
            background.height(background.prop('naturalHeight'));
            background.width(background.prop('naturalWidth'));

            if (background.width() > templateDimensions.width || background.height() > templateDimensions.height) {
                if (background.width() > templateDimensions.width) {
                    var ratio = templateDimensions.width / background.width();

                    background.width(templateDimensions.width);
                    background.height(background.height() * ratio);
                    background.css({
                        left: 0,
                        top: (templateDimensions.height/2.0 - background.height()/2.0) + 'px'
                    });
                }

                if (background.height() > templateDimensions.height) {
                    var ratio = templateDimensions.height / background.height();

                    background.width(background.width() * ratio);
                    background.height(templateDimensions.height);

                    background.css({
                        left: (templateDimensions.width/2.0 - background.width()/2.0) + 'px',
                        top: 0
                    });
                }
            }
            else {
                background.css({
                    left: (templateDimensions.width/2 - background.prop('naturalWidth')/2) + 'px',
                    top: (templateDimensions.height/2 - background.prop('naturalHeight')/2) + 'px'
                });
            }

            bgPosStretch.prop('checked', false);
            bgPosCenter.prop('checked', true);
        }
    }

    function displayBackground(backgroundURL) {
        $j('<img/>', {
            id: 'background',
            src: backgroundURL
        }).css({
            position: 'absolute',
            left: 0,
            top: 0,
            height: templateDimensions.height + 'px',
            width: templateDimensions.width + 'px',
            zIndex: 5
        }).load(function() {
            $j('#loadingIcon').hide();
            setBackgroundPos(backgroundPos);
        }).appendTo('#templateDiv');
    }

    function removeBackground() {
        if (backgroundId != -1) {
            backgroundId = -1;
            $j('#background').remove();
        }
    }

    function unescapeHTML(str) {
        // taken from Prototype
        return str.replace(/<\w+(\s+("[^"]*"|'[^']*'|[^>])+)?>|<\/\w+>/gi, '').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
    }

    $j(document).ready(function() {
        // select items on mousedown
        $j('#templateDiv > div').live('mousedown', function() {
            markSelected($j(this));
        });

        // toggle grid/snap mode
        $j('#snap_checkbox').change(function() {
            snapToGrid = this.checked;
        }).change();

        // show a throbber when uploading a background
        $j('#bgForm').submit(function() {
            $j('#loadingIcon').show();
        });

        $j('#removeBackground').click(function(e) {
            e.preventDefault();
            removeBackground();
        });

        $j('.moveButton').click(function(e) {
            e.preventDefault();
            var dir = $j(this).data('direction');
            moveFuncs[dir]();
        });

        $j('.attrButton').click(function(e) {
            e.preventDefault();
            var attr = $j(this).data('attr');
            attrFuncs[attr]();
        });

        $j('.attrSelect').change(function() {
            var attr = $j(this).data('attr');
            attrFuncs[attr]();
        });

        $j('#changeTemplateSize').click(function(e) {
            e.preventDefault();
            changeTemplateSize();
        });

        $j('#insertButton').click(function(e) {
            e.preventDefault();
            insertElement();
        });

        $j('#removeButton').click(function(e) {
            e.preventDefault();
            removeElement();
        });

        $j('#saveButton').click(function(e) {
            e.preventDefault();
            save();
        });

        $j('#uploadTarget').load(sent);
    });
</script>


<iframe id="uploadTarget" name="uploadTarget" src="" style="width:0px;height:0px;border:0"></iframe>

<div style="width:100%">
  <br/>

  <table class="groupTable" cellpadding="0">
    <tbody>
      <tr>
        <td class="groupTitle" colspan="6">${ titleMessage }</td>
      </tr>
      <tr>
        <td class="titleCellTD">
          <span class="titleCellFormat">Name</span>
        </td>
        <td colspan="5">
          <input id="template_name" size="50" name="Template Name">
        </td>
      </tr>
      <tr>
        <td class="titleCellTD">
          <span class="titleCellFormat">Background</span>
        </td>
        <form id="bgForm" action="${ saveBackgroundURL }" method="POST" enctype="multipart/form-data" target="uploadTarget">
        <td height="20px" NOWRAP align="left" colspan="3">
          <input name="file" size="58" type="file">
          <input class="btn" value="Send File" type="submit">
          <input class="btn" type="button" value="Remove background" id="removeBackground">
        </td>
        <td width="100%" align="left" colspan="4">
          <img id="loadingIcon" src=${ loadingIconURL } width="20px" height="20px" style="display:none;">
        </td>
      </tr>
      <tr>
        <td></td>
        <td>
            <table>
              <tbody>
                <tr><td>
                          <input checked type="radio" id="bgPosStretch" name ='bgPosition' value="Stretch">
                          <label>Stretch</label>
                    </td>
                    <td>
                        <input type='radio' id="bgPosCenter" name ='bgPosition' value="Center">
                        <label>Center</label>
                </td></tr>
              </tbody>
            </table>
        </form>
        </td>
        <td></td>
      </tr>
      <tr>
        <td class="titleCellTD" NOWRAP>
          <span class="titleCellFormat">Poster Width (cm)&nbsp;</span>
        </td>
        <td>
           <input id="poster_width" name="Poster Width" size="5">
        </td>
        <td class="titleCellTD" NOWRAP>
          <span class="titleCellFormat">Poster Height (cm)&nbsp;</span>
        </td>
        <td>
          <input id="poster_height" name="Poster Height" size="5">
          <input class="btn" value="Change" type="button" id="changeTemplateSize">
        </td>
      </tr>
    </tbody>
  </table>

  <br/>

  <table class="groupTable" cellpadding="0" cellspacing="0">

    <tbody>

      <tr>

        <td width="200" rowspan="2" valign="top"> <!-- Width attribute necessary so that the template design space doesn't move depending on selection text-->
          <span class="titleCellFormat">Elements</span>

          <br/><br/>

          <input name="insertButton" id="insertButton" class="btn" value="Insert" type="button">
          <input name="removeButton" id="removeButton" class="btn" value="Remove" type="button" disabled="disabled">

          <br/><br/>

          <select name="Template Elements List" id="elementList">
            ${ selectOptions }
          </select>

          <br/>
          <br/>

          Selection: <span id="selection_text"></span>
          <br/><br/>

          Position:
          <br/>

          <table>
            <tbody>
              <tr>
                <td></td>
                <td align="center">
                  <input name="Move Template Element Top Button" class="btn moveButton" value="Top" type="button" data-direction="top">
                </td>
                <td></td>
              </tr>
              <tr>
                <td align="center">
                  <input name="Move Template Element Left Button" class="btn moveButton" value="Left" type="button" data-direction="left">
                </td>
                <td align="center">
                  <input name="Move Template Element Center Button" class="btn moveButton" value="Center" type="button" data-direction="center">
                </td>
                <td align="center">
                  <input name="Move Template Element Right Button" class="btn moveButton" value="Right" type="button" data-direction="right">
                </td>
              </tr>
              <tr>
                <td></td>
                <td align="center">
                  <input name="Move Template Element Bottom Button" class="btn moveButton" value="Bottom" type="button" data-direction="bottom">
                </td>
                <td></td>
              </tr>
              <tr>
            </tbody>
          </table>

          <input id="snap_checkbox" type="checkbox"/><label for="snap_checkbox">Snap to grid</label>

        </td>

        <td></td>

        <td align="left" valign="bottom" height="22"> <!-- height of the horizontal ruler images -->
          <div id="horizontal_ruler" style="position: relative; height: 5px; top: -6px;">
          </div>
        </td>
      </tr>

      <tr>
        <td valign="top" align="right" width="22"> <!-- width of the vertical ruler image -->
          <div id="vertical_ruler" style="position: relative; width: 5px; left: -6px;">
          </div>
        </td>

        <td align="left" valign="top">
          <div id="templateDiv" style="width:525px;height:742px;position:relative;left:0px;top:0px">
            <table border="1" width="100%" height="100%" cellspacing="0" cellpadding="0">
              <tbody>
                <tr><td></td></tr>
              </tbody>
            </table>
          </div>
        </td>
      </tr>
    </tbody>
  </table>

  <br/>

  <table class="groupTable" cellpadding="0" cellspacing="0">

    <tbody>

      <tr>
        <td colspan="3" rowspan="1" class="titleCellFormat">Attributes</td>
        <td></td>
        <td></td>
      </tr>

      <tr>

       <td class="titleCellTD">
          <span class="titleCellFormat">Font&nbsp;</span>
       </td>

        <td colspan="2">
          <select id='font_selector' name="Template Element Font" class="attrSelect" data-attr="font">
            <optgroup label="Normal Fonts">
              <option>Times New Roman</option>
              <option>Courier</option>
              <option>Sans</option>
            </optgroup>
            <optgroup label="Special Character Fonts">
              <option>LinuxLibertine</option>
              <option>Kochi-Mincho</option>
              <option>Kochi-Gothic</option>
              <option>Uming-CN</option>
              <!--<option>Bitstream Cyberbit</option>-->
            </optgroup>
          </select>
        </td>

        <td class="titleCellTD">
          <span class="titleCellFormat">Color&nbsp;</span>
        </td>

        <td width="100%">
          <select id='color_selector' name="Template Element Color" class="attrSelect" data-attr="color">
            <option>black</option>
            <option>red</option>
            <option>blue</option>
            <option>green</option>
            <option>yellow</option>
            <option>brown</option>
            <option>gold</option>
            <option>pink</option>
            <option>gray</option>
            <option>white</option>
          </select>
        </td>

      </tr>

      <tr>

        <td class="titleCellTD">
          <span class="titleCellFormat">Style&nbsp;</span>
        </td>

        <td colspan="2">
          <select id='style_selector' name="Template Element Style" class="attrSelect" data-attr="style">
            <option value="normal">Normal</option>
            <option value="bold">Bold</option>
            <option value="italic">Italic</option>
            <option value="bold_italic">Bold &amp; Italic</option>
          </select>
        </td>

        <td class="titleCellTD">
          <span class="titleCellFormat">Size&nbsp;</span>
        </td>

        <td width="100%">
          <select id='size_selector' name="Template Element Size" class="attrSelect" data-attr="size">
            <option>160pt</option>
            <option>150pt</option>
            <option>140pt</option>
            <option>130pt</option>
            <option>120pt</option>
            <option>110pt</option>
            <option>100pt</option>
            <option>90pt</option>
            <option>80pt</option>
            <option>70pt</option>
            <option>60pt</option>
            <option>50pt</option>
            <option>40pt</option>
            <option SELECTED>30pt</option>
            <option>20pt</option>
            <option>15pt</option>
            <option>12pt</option>
            <option>10pt</option>
            <option>8pt</option>
          </select>
        </td>
      </tr>

      <tr>
        <td class="titleCellTD">
          <span class="titleCellFormat">Alignment&nbsp;</span>
        </td>
        <td colspan="2">
          <select id='alignment_selector' name="Template Element Alignment" class="attrSelect" data-attr="alignment">
            <!-- Note: the text of the options is used directly in the style attribute of the items -->
            <option>Left</option>
            <option>Right</option>
            <option>Center</option><br>
            <option>Justified</option>
          </select>
        </td>
        <td class="titleCellTD">
          <span class="titleCellFormat">Width (cm)&nbsp;</span>
        </td>
        <td width="100%">
          <input id="width_field" size="5" name="Element Size">
          <input class="btn attrButton" value="Change" type="button" data-attr="width">
        </td>
      </tr>
      <tr>
        <td class="titleCellTD" NOWRAP>
          <span class="titleCellFormat">Text (for Fixed Text)&nbsp;</span>
        </td>
        <td>
          <input id="fixed_text_field" size="30" name="Element Size">
        </td>
        <td>
          <input class="btn attrButton" id="changeText" value="Change" type="button" data-attr="text" />
        </td>
        <td></td>
        <td></td>
      </tr>
    </tbody>
  </table>
  <br/>
  <table class="groupTable">
    <tbody>
      <tr>
        <td colspan="4" align="center" width="100%">
          <input class="btn" name="Save Template Button" value="Save" type="button" id="saveButton">
          <input class="btn" name="Cancel Button" value="Cancel" type="button" onclick="location.href='${ cancelURL }'">
        </td>
      </tr>
    </tbody>
  </table>

  <form id="saveForm" action="${ saveTemplateURL }" method="POST">
      <input name="templateId" value="${ templateId }" type="hidden">
      <input id="templateData" name="templateData" type="hidden">
  </form>

  <script type="text/javascript">

    // We load the template if we are editing a template
    if (${ editingTemplate }) {
        var template = eval(unescapeHTML(${ templateData }));
        $j('#template_name').val(template[0]);
        $j('#templateDiv').width(template[1].width).height(template[1].height);
        items = template[4];
        // We give the toHTML() method to each of the items
        $j.each(items, function(i, item) {
            item.toHTML = Item.prototype.toHTML;
        });
        templateDimensions = new Dimensions(template[1].width, template[1].height);
    } else {
        templateDimensions = new Dimensions(525, 742); //put here the initial dimensions of templateDiv
    }

    previousTemplateDimensions = new Dimensions(0,0);

    $j('#poster_width').val(templateDimensions.width / pixelsPerCm);
    $j('#poster_height').val(templateDimensions.height / pixelsPerCm);

    updateRulers(); // creates the initial rulers
    changeTemplateSize();

    // This function displays the items, if any have been loaded, on the screen
    displayItems();

    if (${ editingTemplate } && ${ hasBackground }) {
        backgroundId = ${ backgroundId };
        backgroundPos = '${ backgroundPos }';
        displayBackground("${ backgroundURL }");
    }

  </script>

</div>
