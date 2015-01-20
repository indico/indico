<script type="text/javascript">

    <%block name="defaults">
        TPL_DEFAULT_SIZE = [425, 270];

        // "Zoom factor" - ratio between font
        // size on screen and on paper
        var zoom_factor = 1;
        var numeric_mode = false;
    </%block>

    var snapToGrid = false;

    // Dimensions of the template space, in pixels
    var templateDimensions;

    // Previous dimensions of the template space, in cm
    var previousTemplateDimensions;

    // Number of pixels per cm
    var pixelsPerCm = 50 * zoom_factor;

    // Id of the background used
    var backgroundId = -1;
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

    // List of template items
    var items = [];

    // Pointer for the jQuery-UI tabs later.
    var controlTabs = null;

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
        this.text = $T("Fixed text");

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
               ' width="' + this.width + '"'  +
               ' style="background-color: '+(this.selected ? "#ccf" : "#fff")+';cursor:move; font-weight:' + (this.bold ? 'bold' : 'normal') + '; font-style:' + (this.italic ? 'italic' : 'normal') +
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
        // -a unique id, which is a natural number (0, 1, 2, ...)
        // -a type (stored in the name attribute)
        // -absolute x,y position
        // -an inner HTML with its content
        itemId++;

        var newDiv = $('<div/>', {
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

    // This function inserts the selected element in the blank space where template designing takes place
    function insertElement() {
        var newDiv = createDiv();
        // We set the inner html of the div depending on the type of item inserted
        switch($('#elementList').val()) {
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
            $('#selection_text').html('');
            lastSelectedDiv = null;
            $('#modify_panel').hide();
            $('#tab_format').hide();
            controlTabs.tabs('option', 'active', 0);

        }
    }

    function markSelected(newSelectedDiv) {
        // Change the text that says which item is selected
        var id = newSelectedDiv.attr('id');
        $('#selection_text').html(translate[items[id].key]);

        // Bring highlight to the element modification tab.
        if (controlTabs) controlTabs.tabs('option', 'active', 1);

        // TODO: add check to see if there's a table inside and not an image

        // Change the background color of the old selected item and the new selected item
        if (lastSelectedDiv) {
            var lastId = lastSelectedDiv.attr('id');
            items[lastId].selected = false;
            lastSelectedDiv.find('> table').css('backgroundColor', '#fff');
        }

        var newSelectedItem = items[id];
        newSelectedItem.selected = true;
        newSelectedDiv.find('> table').css('backgroundColor', '#ccf');
        lastSelectedDiv = newSelectedDiv;

        $('#modify_panel').show();
        $('#tab_format').show();
        // Change the selectors so that they match the properties of the item
        $('#alignment_selector').prop('selectedIndex', newSelectedItem.textAlignIndex);
        $('#font_selector').prop('selectedIndex', newSelectedItem.fontFamilyIndex);
        $('#size_selector').prop('selectedIndex', newSelectedItem.fontSizeIndex);
        $('#style_selector').prop('selectedIndex', newSelectedItem.styleIndex);
        $('#color_selector').prop('selectedIndex', newSelectedItem.colorIndex);
        $('#width_field').val(newSelectedItem.width / pixelsPerCm);

        if (newSelectedItem.key == "Fixed Text") {
            $('#fixedTextContainer').fadeIn();
            $('#fixed_text_field').val(newSelectedItem.text);
        } else {
            $('#fixedTextContainer').fadeOut();
            $('#fixed_text_field').val("");
        }
    }

    function inlineEdit(div) {
        var id = div.attr('id');
        var selectedItem = items[id];

        // Handle the individual cases as required.
        if (selectedItem.key == "Fixed Text") {
            var text = prompt("Enter fixed-text value", selectedItem.text);

            if (text) {
                selectedItem.text = text;
                div.html(selectedItem.toHTML());

                markSelected(div); // Update the fixed-text field
            }
        }
    }

    function updateRulers() {
        if (templateDimensions.width > previousTemplateDimensions.width) {
            var hRuler = $('#horizontal_ruler');
            for (var i = Math.ceil(previousTemplateDimensions.width / pixelsPerCm); i < Math.ceil(templateDimensions.width / pixelsPerCm); i++) {

                $('<div class="marking"/>', {
                     id: 'rulerh' + i
                }).css({
                    width: pixelsPerCm + 'px',
                    left: (i * pixelsPerCm) + 'px',
                    top: 0
                }).html(i + 1).appendTo(hRuler);
            }
        }
        else if (templateDimensions.width < previousTemplateDimensions.width) {
            for (var i = Math.ceil(previousTemplateDimensions.width / pixelsPerCm); i > Math.ceil(templateDimensions.width / pixelsPerCm); i--) {
                $('#horizontal_ruler' + (i - 1)).remove();
            }
        }

        if (templateDimensions.height > previousTemplateDimensions.height) {
            var vRuler = $('#vertical_ruler');
            for (var i = Math.ceil(previousTemplateDimensions.height / pixelsPerCm); i < Math.ceil(templateDimensions.height / pixelsPerCm); i++) {
                $('<div class="marking"/>', {
                    id: 'rulerv' + i
                }).css({
                    'line-height': pixelsPerCm/2.0 + 'px',
                    height: pixelsPerCm  + 'px',
                    left: 0,
                    top: (i * pixelsPerCm) + 'px'
                }).html(i + 1).appendTo(vRuler);
            }
        }
        else if (templateDimensions.height < previousTemplateDimensions.height) {
            for (i = Math.ceil(previousTemplateDimensions.height / pixelsPerCm); i > Math.ceil(templateDimensions.height / pixelsPerCm); i--) {
                $('#vertical_ruler > #rulerv' + (i - 1)).remove();
            }
        }
    }

    // This function displays all the items in the 'items' array on the screen
    // If there are already some items being displayed, it does not erase them
    function displayItems() {
        $.each(items, function(i, item) {
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
        var tpl = $('#templateDiv');
        tpl.width($('#badge_width').val() * pixelsPerCm);
        tpl.height($('#badge_height').val() * pixelsPerCm);
        previousTemplateDimensions.width = templateDimensions.width;
        previousTemplateDimensions.height = templateDimensions.height;
        templateDimensions = new Dimensions($('#badge_width').val() * pixelsPerCm, $('#badge_height').val() * pixelsPerCm);
        updateRulers();
        if (backgroundId != -1) {
            var url = $('#background').attr('src');
            $('#background').remove();
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
                item.fontFamily = $('#font_selector').val();
                item.fontFamilyIndex = $('#font_selector').prop('selectedIndex');
                lastSelectedDiv.html(item.toHTML());
            }
        },
        color: function() {
            if (lastSelectedDiv) {
                var item = items[lastSelectedDiv.attr('id')];
                item.color = $('#color_selector').val();
                item.colorIndex = $('#color_selector').prop('selectedIndex');
                lastSelectedDiv.html(item.toHTML());
            }
        },
        alignment: function() {
            if (lastSelectedDiv) {
                var item = items[lastSelectedDiv.attr('id')];
                item.textAlign = $('#alignment_selector').val();
                item.textAlignIndex = $('#alignment_selector').prop('selectedIndex');
                lastSelectedDiv.html(item.toHTML());
            }
        },
        size: function() {
            if (lastSelectedDiv) {
                var item = items[lastSelectedDiv.attr('id')];
                item.fontSize = zoom_font(zoom_factor, $('#size_selector').val());
                item.fontSizeIndex = $('#size_selector').prop('selectedIndex');
                lastSelectedDiv.html(item.toHTML());
            }
        },
        style: function() {
            if (lastSelectedDiv) {
                var item = items[lastSelectedDiv.attr('id')];
                switch($('#style_selector').val()) {
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

                item.styleIndex = $('#style_selector').prop('selectedIndex');
                lastSelectedDiv.html(item.toHTML());
            }
        },
        text: function() {
            if (lastSelectedDiv) {
                var item = items[lastSelectedDiv.attr('id')];
                item.text = unescapeHTML($('#fixed_text_field').val());
                $('#fixed_text_field').val(item.text);
                lastSelectedDiv.html(item.toHTML());
            }
        },
        width: function() {
            if (lastSelectedDiv) {
                var item = items[lastSelectedDiv.attr('id')];
                item.width = $('#width_field').val() * pixelsPerCm;
                lastSelectedDiv.html(item.toHTML());
            }
        }
    };

    function zoom_font(zfact, fontSize) {
        if (numeric_mode) {
            var pattern = /([0-9.]+)pt/g
            var ftsize = pattern.exec(fontSize)[1];
            return (ftsize * zfact) + 'pt';
        } else {
            return fontSize;
        }
    }

    function save() {
        if ($('#template_name').val() == '') {
            new AlertPopup($T("Warning"), $T("Please choose a name for the template")).open();
            return;
        }
        var template = [];
        template.push($('#template_name').val());
        template.push(templateDimensions, pixelsPerCm);
        template.push(backgroundId);

        $.each(items, function(i, item) {
            if (item != false) {
                item.fontSize = zoom_font(1/zoom_factor, item.fontSize);
            }
        });

        template.push(items);
        $('#templateData').val(Json.write(template));
        $('#saveForm').submit();
    }

    function setBackgroundPos(mode) {
        var background = $('#background');
        var hiddenField = $('#bgPosition');
        var bgPosStretch = $('#bgPosStretch');
        var bgPosCenter = $('#bgPosCenter');

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
        $('<img/>', {
            id: 'background',
            src: backgroundURL
        }).css({
            position: 'absolute',
            left: 0,
            top: 0,
            height: templateDimensions.height + 'px',
            width: templateDimensions.width + 'px',
            zIndex: 5
        }).on('load', function() {
            $('#loadingIcon').hide();
            $('#removeBackground').removeClass('hidden');
            setBackgroundPos(backgroundPos);
        }).appendTo('#templateDiv');
    }

    function removeBackground() {
        if (backgroundId != -1) {
            backgroundId = -1;
            $('#background').remove();
            $('#removeBackground').addClass('hidden');
        }
    }

    function unescapeHTML(str) {
        // taken from Prototype
        return str.replace(/<\w+(\s+("[^"]*"|'[^']*'|[^>])+)?>|<\/\w+>/gi, '').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g,'&');
    }

    $(document).ready(function() {

        $('#bgForm input[type="file"]').on('change', function() {
          var $this = $(this);
          if ($this.val()) {
            $('#uploadBackground').removeClass('hidden');
          } else {
            $('#uploadBackground').addClass('hidden');
          }

        });


        if (backgroundId != -1) {
            $('#removeBackground').removeClass('hidden');
        }

        // select and inline edit
        $('#templateDiv').on('mousedown', 'div', function() {
            markSelected($(this));
        }).on('dblclick', 'div', function() {
            inlineEdit($(this));
        });

        $('#uploadBackground').click(function() {
            $('#bgForm').submit();
            return false;
        });

        // toggle grid/snap mode
        $('#snap_checkbox').change(function() {
            snapToGrid = this.checked;
        }).change();

        $('#bgForm').ajaxForm({
            dataType: 'json',
            iframe: true,
            success: function(data) {
                if(data.status != 'OK') {
                    new AlertPopup($T("Error"), $T("An error occurred")).open();
                    $('#loadingIcon').hide();
                    return;
                }
                if (backgroundId != -1) {
                    $('#background').remove();
                }
                backgroundId = data.id;
                backgroundPos = data.pos;
                displayBackground(data.url);
            },
            beforeSubmit: function() {
                $('#loadingIcon').show();
            }
        });

        $('#removeBackground').click(function(e) {
            e.preventDefault();
            removeBackground();
        });

        $('.moveButton').click(function(e) {
            e.preventDefault();
            var dir = $(this).data('direction');
            moveFuncs[dir]();
        });

        $('.attrButton').click(function(e) {
            e.preventDefault();
            var attr = $(this).data('attr');
            attrFuncs[attr]();
        });

        $('.attrSelect').change(function() {
            var attr = $(this).data('attr');
            attrFuncs[attr]();
        });

        $('#changeTemplateSize').click(function(e) {
            e.preventDefault();
            changeTemplateSize();
        });

        $('#insertButton').click(function(e) {
            e.preventDefault();
            insertElement();
        });

        $('#removeButton').click(function(e) {
            e.preventDefault();
            removeElement();
        });

        $('#saveButton').click(function(e) {
            e.preventDefault();
            save();
        });

        controlTabs = $('#controlTabs').tabs();
    });
</script>

<!-- CONTEXT HELP DIVS -->
<div id="tooltipPool" style="display: none">
    <!-- Where is key? -->
    <div id="features" class="tip">
        <b>FullName can have four different formats:</b><br>
        - <b>FullName</b>: Mr. DOE, Jonh<br>
        - <b>Full Name (w/o title)</b>: DOE, Jonh<br>
        - <b>FullName B</b>: Mr. Jonh Doe<br>
        - <b>FullName B Full Name (w/o title)</b>: Jonh Doe<br>
    </div>
</div>
<!-- END OF CONTEXT HELP DIVS -->

<div style="width:100%">
    <div class="groupTitle">
        ${titleMessage}
    </div>

    <!-- Save Document Options -->
    <div class="overflow">
      ${_('Once you have finished designing, you may either save or discard your changes here.')}
      <div style="float:right;">
          <input class="i-button accept" name="Save Template Button" value="${ _("Save Template")}" type="button" id="saveButton" />
          <input class="i-button" name="Cancel Button" value="${ _("Cancel")}" type="button" onclick="location.href='${cancelURL}'" />

          <form id="saveForm" action="${saveTemplateURL}" method="POST">
              <input name="templateId" value="${templateId}" type="hidden">
              <input id="templateData" name="templateData" type="hidden">
          </form>
      </div>
      <div class="toolbar-clearer"></div>
    </div>

    <!-- Tabulated controls -->
    <div id="controlTabs">
        <ul>
            <li><a href="#tabsGeneral">${_('General Settings &amp; Layout')}</a></li>
            <li id="tab_format"><a href="#tabsFormatting">${_('Element Formatting')}</a></li>
        </ul>

        <!-- Tab for badge paramaters -->
        <div id="tabsGeneral" class="tab">
            <div class="left panel">
                <i class="icon-wrench left" title="${_("Template settings")}"></i>
                <div class="content">
                  <h4>${_('Template Name')}</h4>
                  <input id="template_name" size="30" name="Template Name" />
                </div>
            </div>
            <div class="left panel">
              <i class="icon-rulers left" title="${_("Template dimensions")}"></i>
                <div class="content">
                  <div class="left">${_('Width')} <input id="badge_width" name="Badge Width" size="5" style="margin-left: 0.5em;"></div>
                  <div class="left clear">${_('Height')}<input id="badge_height" name="Badge Height" size="5" style="margin-left: 0.5em;"></div>
                  <div class="clear"></div>
                  <div class="text-not-important" style="margin-top: 1em;">${_("Dimensions are in cm, decimals are allowed.")}</div>
                  <div style="margin-top: 1em;"><input id="snap_checkbox" type="checkbox"/><label for="snap_checkbox">${ _("Snap to grid")}</label></div>
                </div>
            </div>

            <div class="left panel">
              <i class="icon-pictures left" title="${_("Background")}"></i>
              <form id="bgForm" action="${ saveBackgroundURL }" method="POST" enctype="multipart/form-data" class="left">
                <input name="file" type="file" style="margin-bottom: 1em;" />
                <%block name="background_options">
                </%block>
                <div class="toolbar">
                  <div class="group">
                    <a class="i-button icon-upload icon-only hidden" id="uploadBackground" title="${_("Upload file")}"></a>
                    <a class="i-button icon-remove icon-only hidden" id="removeBackground" title="${_("Remove background")}"></a>
                      </div>
                </div>
              </form>
              <img id="loadingIcon" src=${loadingIconURL} style="display:none; width: 20px; height: 20px;" />
            </div>

        </div>
        <!-- Tab for element formatting -->
        <div id="tabsFormatting" class="tab">
            <div class="left panel">
                <i class="icon-font-size left" title="${_("Font definitions")}"></i>
                <!-- Font Face -->
                <div class="content">
                    <select id='font_selector' name="Template Element Font" class="attrSelect" data-attr="font">
                      <optgroup label="${ _('Normal Fonts') }">
                        <option>Times New Roman</option>
                        <option>Courier</option>
                        <option>Sans</option>
                      </optgroup>
                      <optgroup label="${ _('Special Character Fonts') }">
                        <option>LinuxLibertine</option>
                        <option>Kochi-Mincho</option>
                        <option>Kochi-Gothic</option>
                        <option>Uming-CN</option>
                      </optgroup>
                    </select>
                    <!-- Font Colour -->
                    <select id='color_selector' name="Template Element Color" class="attrSelect" data-attr="color">
                      <option value="black"> ${ _("black")}</option>
                      <option value="red"> ${ _("red")}</option>
                      <option value="blue"> ${ _("blue")}</option>
                      <option value="green"> ${ _("green")}</option>
                      <option value="yellow"> ${ _("yellow")}</option>
                      <option value="brown"> ${ _("brown")}</option>
                      <option value="gold"> ${ _("gold")}</option>
                      <option value="pink"> ${ _("pink")}</option>
                      <option value="gray"> ${ _("gray")}</option>
                      <option value="white"> ${ _("white")}</option>
                    </select>
                    <!-- Font Style -->
                    <select id='style_selector' name="Template Element Style" class="attrSelect" data-attr="style">
                      <option value="normal"> ${ _("Normal")}</option>
                      <option value="bold"> ${ _("Bold")}</option>
                      <option value="italic"> ${ _("Italic")}</option>
                      <option value="bold_italic"> ${ _("Bold &amp; Italic")}</option>
                    </select>
                    <!-- Font Size -->
                    <select id='size_selector' name="Template Element Size" class="attrSelect" data-attr="size">
                        <%block name="font_sizes">
                            <option value="xx-small"> ${ _("xx-small")}</option>
                            <option value="x-small"> ${ _("x-small")}</option>
                            <option value="small"> ${ _("small")}</option>
                            <option value="medium" SELECTED> ${ _("medium")}</option>
                            <option value="large"> ${ _("large")}</option>
                            <option value="x-large"> ${ _("x-large")}</option>
                            <option value="xx-large"> ${ _("xx-large")}</option>
                        </%block>
                </select>
                <!-- Font Alignment -->
                <select id='alignment_selector' name="Template Element Alignment" class="attrSelect" data-attr="alignment">
                    <!-- Note: the value of the options is used directly in the style attribute of the items -->
                    <option value="Left"> ${ _("Left")}</option>
                    <option value="Right"> ${ _("Right")}</option>
                    <option value="Center"> ${ _("Center")}</option>
                    <option value="Justified"> ${ _("Justified")}</option>
                </select>
            </div>
        </div>

            <div class="left panel">
              <i class="icon-rulers left" title="${_("Element dimensions")}"></i>
              <div class="content">
              Width <input id="width_field" size="5" name="Element Size" />
              <h4>${ _("Positioning")}</h4>
              <table width="90%">
                <tbody>
                  <tr>
                    <td></td>
                    <td align="center">
                      <input name="Move Template Element Top Button" class="btn moveButton" value="${ _("Top")}" type="button" data-direction="top" />
                    </td>
                    <td></td>
                  </tr>
                  <tr>
                    <td align="center">
                      <input name="Move Template Element Left Button" class="btn moveButton" value="${ _("Left")}" type="button" data-direction="left"/>
                    </td>
                    <td align="center">
                      <input name="Move Template Element Center Button" class="btn moveButton" value="${ _("Center")}" type="button" data-direction="center"/>
                    </td>
                    <td align="center">
                      <input name="Move Template Element Right Button" class="btn moveButton" value="${ _("Right")}" type="button" data-direction="right"/>
                    </td>
                  </tr>
                  <tr>
                    <td></td>
                    <td align="center">
                      <input name="Move Template Element Bottom Button" class="btn moveButton" value="${ _("Bottom")}" type="button" data-direction="bottom"/>
                    </td>
                   <td></td>
                  </tr>
                </tbody>
              </table>
              </div>
            </div>

            <div class="left panel" id="fixedTextContainer" style="display:none; margin-left: 1em;">
              <i class="icon-type left" title="${_("Text")}"></i>
              <input id="fixed_text_field" size="30" name="Element Text" placeholder="${_("Insert your text here")}"/>
            </div>
          </div>
          <!-- End of formatting tab -->
        </div>

  <table class="groupTable" border="0" cellpadding="0" cellspacing="0">
    <tbody>
      <tr>
        <td rowspan="2" id="controls"> <!-- Width attribute necessary so that the template design space doesn't move depending on selection text-->

        <!-- Insert Elements -->
        <div class="panel">
            <h3>${_('Insert Elements')}</h3>
              <select name="Template Elements List" id="elementList">
                ${selectOptions}
              </select>
            <a id="insertButton" class="i-button icon-plus right icon-only" title="${ _("Insert")}"></a>
        </div>
        <!-- Modify Selected Element -->
        <div id="modify_panel" class="panel overflow clear" style="display: none;">

          <div class="overflow">
            <h3>${_('Selected Element')}</h3>
            <div id="selection_text" class="left">
            </div>
            <a id="removeButton" class="right i-button icon-remove icon-only" title="${ _("Remove Element")}"></a>
          </div>
        </td>

        <td></td>

        <td align="left" valign="bottom" height="22px"> <!-- height of the horizontal ruler images -->
            <div id="horizontal_ruler" class="ruler">
            </div>
        </td>
      </tr>

      <tr>
        <td valign="top" align="right" width="22px"> <!-- width of the vertical ruler image -->
            <div id="vertical_ruler" class="ruler">
            </div>
        </td>

        <td align="left" valign="top">
          <div id="templateDiv" style="width:425px;height:270px;position:relative;left:0px;top:0px"> <!-- put here the initial dimensions of templateDiv -->
            <table border="1" style="border-style: none;" width="100%" height="100%" cellspacing="0" cellpadding="0">
              <tbody>
                <tr><td></td></tr>
              </tbody>
            </table>
          </div>

        </div>

        </td>
      </tr>
    </tbody>
  </table>

  <script type="text/javascript">
    // We load the template if we are editing a template
    if (${ editingTemplate }) {
        var template = ${ templateData };
        $('#template_name').val(template[0]);
        $('#templateDiv').width(template[1].width).height(template[1].height);
        items = template[4];
        // We give the toHTML() method to each of the items
        $.each(items, function(i, item) {
            item.toHTML = Item.prototype.toHTML;
        });
        templateDimensions = new Dimensions(template[1].width, template[1].height);
    } else {
        templateDimensions = new Dimensions(TPL_DEFAULT_SIZE[0], TPL_DEFAULT_SIZE[1]);
    }

    previousTemplateDimensions = new Dimensions(0,0);

    $('#badge_width').val(templateDimensions.width / pixelsPerCm);
    $('#badge_height').val(templateDimensions.height / pixelsPerCm);

    $('#badge_width, #badge_height').on('keyup', function() {
        changeTemplateSize();
    });

    $('#width_field').on('keyup', function() {
        attrFuncs['width']();
    });

    $('#fixed_text_field').on('keyup', function() {
        attrFuncs['text']();
    });

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
