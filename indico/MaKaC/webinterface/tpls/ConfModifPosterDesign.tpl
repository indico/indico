  <script type="text/javascript">

    // "Zoom factor" - the size of the document, related to reality

    var zoom_factor = 0.5

    // These variables are initialised by a script at the end of the document
    // They represent the top left corner of the blank space where poster template design takes place
    var xBlankSpace = 0;
    var yBlankSpace = 0;

    // Dimensions of the template space, in pixels
    var templateDimensions;

    // Previous dimensions of the template space, in cm
    var previousTemplateDimensions;

    // Number of pixels per cm
    var pixelsPerCm = 50 * zoom_factor;

    // Id of the background used
    var backgroundId = -1

    // Number of pixels, both horizontal and vertical, that are between the top left corner
    // and the position where items are inserted
    var initialOffset = pixelsPerCm;

    // Id of the next element to be inserted
    var itemId = -1;

    // Common parts of many elements
    var elementCommon1 = '<table border="2" cellpadding="0" cellspacing="0" style="cursor:move;" onClick=clicked(event) width="200"><tbody><tr><td align="center">';
    var elementCommon2 = '</td></tr></tbody></table>';

    // Last selected item (holds the div for that item)
    var lastSelectedDiv;

    // Translation dictionary from key to name in current language.
    var translate = <%=translateName%>;

    // List of poster template items
    var items = [];

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
        return '<table border="2" cellpadding="0" cellspacing="0" onClick=clicked(event)' +
              ' width="' + this.width + '" bgColor="' + (this.selected? "#CCCCFF" : "white") +
              '" style="cursor:move; font-weight:' + (this.bold ? 'bold' : 'normal') + '; font-style:' + (this.italic ? 'italic' : 'normal') +
              '; text-align: ' + this.textAlign + ';"' +
              '><tbody><tr><td><span style="color:' + this.color + '; font-family: ' + this.fontFamily + '; font-size:' + this.fontSize + ';">' +
              (this.key == "Fixed Text" ? this.text : translate[this.key]) +
              '</span></td></tr></tbody></table>';
      }

    // Dimensions class
    function Dimensions(width, height) {
      this.width = width
      this.height = height
    }

    // Returns the first div encountered when exploring the PARENT nodes of the element
    function getDiv (element) {
      if (element.tagName == "DIV") {
        return element;
      }
      if (element.tagName == "BODY") {
        return false;
      }
      return getDiv(element.parentNode);
    }

    // Function object that will be passed to draggables when we want them to snap to a grid
    var mySnap = function(x,y) {

        var xResolution = 10;
        var yResolution = 10;

        xResult = Math.floor(x / xResolution) * xResolution;
        yResult = Math.floor(y / yResolution) * yResolution;

        return [xResult,yResult];
    }

    // This function creates a new draggable div
    function createDiv() {
    //       Each div has:
    //       -an unique id, which is a natural number (0, 1, 2, ...)
    //       -a type (stored in the name attribute)
    //       -absolute x,y position
    //       -an inner HTML with its content
      itemId++;

      var newDiv = document.createElement('div');

      newDiv.id = itemId;
      newDiv.style.position="absolute";
      newDiv.style.left=initialOffset+"px";
      newDiv.style.top=initialOffset+"px";
      newDiv.style.zIndex = itemId + 10

      // We insert the div in the HTML document
      $("templateDiv").appendChild(newDiv);

      // We create a Draggable from the div
      var newDrag = new Draggable(newDiv.id , { // Scriptaculous class

        revert:false,

        endeffect: function(element) { // We overload this function, writing the original code + our code. Element is a div

          // Begining of original code
          var toOpacity = typeof element._opacity == 'number' ? element._opacity : 1.0
          new Effect.Opacity(element, {duration:0.2, from:0.7, to:toOpacity});
          // End of original code

          // The following code returns the dragged item inside the template area if it's dragged outside
          var offset = Position.cumulativeOffset(element); // Prototype function
          var dimensions = Element.getDimensions(element); // Prototype function

          if (!Position.within($('templateDiv'), offset[0], offset[1]) || // Prototype function
              !Position.within($('templateDiv'), offset[0] + dimensions.width - 1, offset[1] + dimensions.height - 1)) {
            // Element is OUTSIDE the template design space, we restore the previous position
            element.style.left = element.lastGoodPositionLeft;
            element.style.top = element.lastGoodPositionTop;
          } else {
            // Element is INSIDE the template design space, we save the position
            element.lastGoodPositionLeft = element.style.left;
            element.lastGoodPositionTop = element.style.top;
          }

          // The following code saves the position of the div
          items[element.id].x = element.lastGoodPositionLeft;
          items[element.id].y = element.lastGoodPositionTop;

        },

        snap: ($F('snap checkbox') == "on") ? mySnap : false
      });

      // We store the initial position as a good position which to return to
      newDiv.lastGoodPositionLeft = 0;
      newDiv.lastGoodPositionTop = 0;

      return newDiv;
    }

    // This function inserts the selected element in the blank space where poster template designing takes place
    function insertElement() {

      newDiv = createDiv()

      // We set the inner html of the div depending on the type of item inserted
      switch($F('elementList')) {
        %(switchCases)s
      }

      if (!lastSelectedDiv) {
        markSelected(newDiv);
      }

      initialOffset += 10

    }

    function removeElement() {
      if(lastSelectedDiv) {
        items[lastSelectedDiv.id] = false;
        Element.remove(lastSelectedDiv); // Prototype function
        $('selection text').innerHTML = "";
        lastSelectedDiv = false;
      }
    }

    /*
    The following method does not work in IE because of $('font selector').options[i].value .
    As well, it seems the function is not needed and it was just used once in the method markSelected, like this:

        $('font selector').selectedIndex = getSelectedFontIndex(newSelectedItem);

    we replaced it with:

        $('font selector').selectedIndex = newSelectedItem.fontFamilyIndex;

    function getSelectedFontIndex(newSelectedItem) {
        index = 0;
        for (i = 0; i < $('font selector').options.length; i++) {
            if ($('font selector').options[i].value == newSelectedItem.fontFamily) {
                index = newSelectedItem.fontFamilyIndex;
            }
        }
        return index;
    }*/

    function markSelected(newSelectedDiv) {

      // Change the text that says which item is selected
      $('selection text').innerHTML = translate[items[newSelectedDiv.id].key];

      // TODO: add check to see if there's a table inside and not an image

      // Change the background color of the old selected item and the new selected item
      if (lastSelectedDiv) {
        items[lastSelectedDiv.id].selected = false;
        lastSelectedDiv.innerHTML = items[lastSelectedDiv.id].toHTML();
      }

      var newSelectedItem = items[newSelectedDiv.id];
      newSelectedItem.selected = true;
      newSelectedDiv.innerHTML = newSelectedItem.toHTML();
      lastSelectedDiv = newSelectedDiv;

      // Change the selectors so that they match the properties of the item
      $('alignment selector').selectedIndex = newSelectedItem.textAlignIndex;
      $('font selector').selectedIndex = newSelectedItem.fontFamilyIndex;
      $('size selector').selectedIndex = newSelectedItem.fontSizeIndex;
      $('style selector').selectedIndex = newSelectedItem.styleIndex;
      $('color selector').selectedIndex = newSelectedItem.colorIndex;
      $('width field').value = newSelectedItem.width / pixelsPerCm;
      if (newSelectedItem.key == "Fixed Text") {
        $('fixed text field').value = newSelectedItem.text
      } else {
          $('fixed text field').value = "--"
      }
    }

    function clicked(event) {
      markSelected(getDiv(Event.element(event))); // Prototype function
    }

    function updateRulers() {
      var horizontalRuler = $('horizontal ruler');
      var horizontalRuler = $('vertical ruler');

      if (templateDimensions.width > previousTemplateDimensions.width) {
           var hRuler = $('horizontal ruler');

        for (i = Math.ceil(previousTemplateDimensions.width / pixelsPerCm); i < Math.ceil(templateDimensions.width / pixelsPerCm); i++) {
          var newImg = document.createElement('div');
          newImg.id = "rulerh" + i;
          newImg.style.width = pixelsPerCm-1 + 'px';
          newImg.style.height = '10px';
          newImg.style.position = 'absolute';
          newImg.style.border = '1px solid black';
          newImg.style.borderTop = 'none';
          newImg.style.background = '#EEEEEE';
          newImg.style.textAlign = 'right';
          newImg.style.fontSize = '6pt';
          newImg.style.left =  i*pixelsPerCm-1 + 'px';
          newImg.style.top =  0;
          newImg.innerHTML =i+1;
          hRuler.appendChild(newImg);
        }
      } else if (templateDimensions.width < previousTemplateDimensions.width) {
        for (i = Math.ceil(previousTemplateDimensions.width / pixelsPerCm); i > Math.ceil(templateDimensions.width / pixelsPerCm); i = i - 1) {
          $('horizontal ruler').removeChild($('rulerh' + (i - 1)));
        }
      }

      if (templateDimensions.height > previousTemplateDimensions.height) {
           var vRuler = $('vertical ruler');

        for (i = Math.ceil(previousTemplateDimensions.height / pixelsPerCm); i < Math.ceil(templateDimensions.height / pixelsPerCm); i++) {
          var newImg = document.createElement('div');
          newImg.id = "rulerv" + i;
          newImg.style.height = pixelsPerCm-1 + 'px';
          newImg.style.width = '10px';
          newImg.style.position = 'absolute';
          newImg.style.border = '1px solid black';
          newImg.style.borderLeft = 'none';
          newImg.style.background = '#EEEEEE';
          newImg.style.verticalAlign = 'bottom';
          newImg.style.fontSize = '6pt';
          newImg.style.top = i*pixelsPerCm-1 + 'px';
          newImg.style.left =  0;
          newImg.innerHTML ='<p style="font-size: 6pt; margin-bottom: 0px;">'+(i+1)+'</p>';
          vRuler.appendChild(newImg);
        }
      } else if (templateDimensions.height < previousTemplateDimensions.height) {
        for (i = Math.ceil(previousTemplateDimensions.height / pixelsPerCm); i > Math.ceil(templateDimensions.height / pixelsPerCm); i = i - 1) {
          $('vertical ruler').removeChild($('rulerv' + (i - 1)));
        }
      }

    }

    // This function displays all the items in the 'items' array on the screen
    // If there are already some items being displayed, it does not erase them
    function displayItems() {
      items.each( function (item) { //Prototype-like loop
        newDiv = createDiv();
        newDiv.style.left = item.x + "px";
        newDiv.style.top = item.y + "px";
        item.fontSize = zoom_font(zoom_factor,item.fontSize);
        newDiv.innerHTML = item.toHTML();
        if (item.selected) {
          markSelected(newDiv)
          lastSelectedDiv = newDiv
        }
      });
    }


    function changeTemplateSize() {
      $('templateDiv').style.width = $F('poster width') * pixelsPerCm  + "px";
      $('templateDiv').style.height = $F('poster height') * pixelsPerCm  + "px";
      previousTemplateDimensions.width = templateDimensions.width;
      previousTemplateDimensions.height = templateDimensions.height;
      templateDimensions = new Dimensions($F('poster width') * pixelsPerCm, $F('poster height') * pixelsPerCm);
      updateRulers();
      if (backgroundId != -1) {
        var url = $('background').src
        Element.remove('background')
        displayBackground(url)
      }
    }

    function moveLeft() {
      if(lastSelectedDiv) {
        lastSelectedDiv.style.left = 0  + "px";
        items[lastSelectedDiv.id].x = 0  + "px";
      }
    }

    function moveRight() {
      if(lastSelectedDiv) {
        var itemDimensions = Element.getDimensions(lastSelectedDiv); //Prototype function
        lastSelectedDiv.style.left = templateDimensions.width - itemDimensions.width - 1  + "px"; // -1 because of the table border
        items[lastSelectedDiv.id].x = templateDimensions.width - itemDimensions.width - 1  + "px";
      }
    }

    function moveCenter() {
      if(lastSelectedDiv) {
        var itemDimensions = Element.getDimensions(lastSelectedDiv); //Prototype function
        lastSelectedDiv.style.left = (templateDimensions.width - itemDimensions.width - 1) / 2  + "px";
        lastSelectedDiv.style.top = (templateDimensions.height - itemDimensions.height - 1) / 2  + "px";
        items[lastSelectedDiv.id].x = (templateDimensions.width - itemDimensions.width - 1) / 2  + "px";
        items[lastSelectedDiv.id].y = (templateDimensions.height - itemDimensions.height - 1) / 2  + "px";
      }
    }

    function moveTop() {
      if(lastSelectedDiv) {
        lastSelectedDiv.style.top = 0  + "px";
        items[lastSelectedDiv.id].y = 0  + "px";
      }
    }

    function moveBottom() {
      if(lastSelectedDiv) {
        var itemDimensions = Element.getDimensions(lastSelectedDiv); //Prototype function
        lastSelectedDiv.style.top = templateDimensions.height - itemDimensions.height - 1 + "px";
        items[lastSelectedDiv.id].y = templateDimensions.height - itemDimensions.height - 1  + "px";
      }
    }

    function snapToGrid() {
      if ($F('snap checkbox') == "on") {
        for (i = 0; i < Draggables.drags.length; i++) { //Draggables is the object where scriptaculous stores draggable objects
          Draggables.drags[i].options.snap = mySnap; // TODO; snap from the top left corner; define function(x,y) {} instead of [10,10]
        }
      } else {
        for (i = 0; i < Draggables.drags.length; i++) {
          Draggables.drags[i].options.snap = false;
        }
      }
    }

    function changeAlignment() {
      if(lastSelectedDiv) {
        var item = items[lastSelectedDiv.id];
        item.textAlign = $F('alignment selector');
        item.textAlignIndex = $('alignment selector').selectedIndex;
        lastSelectedDiv.innerHTML = item.toHTML();
      }
    }

    function changeFont() {
      if(lastSelectedDiv) {
        var item = items[lastSelectedDiv.id];
        item.fontFamily = $F('font selector');
        item.fontFamilyIndex = $('font selector').selectedIndex;
        lastSelectedDiv.innerHTML = item.toHTML();
      }
    }

    function zoom_font(zfact,fontSize)
    {
        var pattern = new RegExp ("([0-9.]+)pt", "g");

        var ftsize = pattern.exec(fontSize)[1];

        return (ftsize*zfact)+"pt";
    }

    function changeSize() {
      if(lastSelectedDiv) {
        var item = items[lastSelectedDiv.id];
        item.fontSize = zoom_font(zoom_factor,$F('size selector'));
        item.fontSizeIndex = $('size selector').selectedIndex;
        lastSelectedDiv.innerHTML = item.toHTML();
      }
    }

    function changeStyle() {
      if(lastSelectedDiv) {
        var item = items[lastSelectedDiv.id];
        switch($F('style selector')) {
          case "Normal":
            item.bold = false;
            item.italic = false10;
            break;
          case "Bold":
            item.bold = true;
            item.italic = false;
            break;

          case "Italic":
            item.bold = false;
            item.italic = true;
            break;

          case "Bold & Italic":
            item.bold = true;
            item.italic = true;
            break;
        }

        item.styleIndex = $('style selector').selectedIndex;
        lastSelectedDiv.innerHTML = item.toHTML();
      }
    }

    function changeColor() {
      if(lastSelectedDiv) {
        var item = items[lastSelectedDiv.id];
        item.color = $F('color selector');
        item.colorIndex = $('color selector').selectedIndex;
        lastSelectedDiv.innerHTML = item.toHTML();
      }
    }

    function changeWidth() {
      if(lastSelectedDiv) {
        var item = items[lastSelectedDiv.id];
        item.width = $F('width field') * pixelsPerCm;
        lastSelectedDiv.innerHTML = item.toHTML();
      }
    }

    function changeText() {
      if(lastSelectedDiv) {
        var item = items[lastSelectedDiv.id]
        item.text = $F('fixed text field').unescapeHTML()
        lastSelectedDiv.innerHTML = item.toHTML()
      }
    }

    function save() {
      if ($F('template name') == '') {
        alert("Please choose a name for the template")
        return
      }
      template = [];
      template.push($F('template name'));
      template.push(templateDimensions, pixelsPerCm);
      template.push(backgroundId);

      for (var i=0;i<items.length;++i)
      {
          if (items[i] != false)
              items[i].fontSize = zoom_font(1/zoom_factor,items[i].fontSize);
      }

      template.push(items);
      $('templateData').value = template.toJSON();
      document.hiddenform.submit()
    }

    function sending() {
      Element.show('loadingIcon')
    }

    firstLoad = true

    function sent() {
      if (firstLoad) {
        firstLoad = false
      } else {
        var iframeDocument = $('uploadTarget').contentDocument || $('uploadTarget').contentWindow
        if (iframeDocument.document) {
          iframeDocument = iframeDocument.document
        }

        try {
          if (backgroundId != -1) {
            Element.remove('background')
          }
          backgroundId = iframeDocument.getElementById('background id').innerHTML
          var backgroundURL = iframeDocument.getElementById('background url').innerHTML

          backgroundPos = iframeDocument.getElementById('background pos').innerHTML

          displayBackground(backgroundURL);



        } catch (err) {
          Element.hide('loadingIcon')
        }
      }
    }


    function setBackgroundPos(mode)
    {
        var background = document.getElementById('background');
        var hiddenField = document.getElementById('bgPosition');

        var bgPosStretch = document.getElementById('bgPosStretch');
        var bgPosCenter = document.getElementById('bgPosCenter');


        if (mode == 'Stretch')
        {
            background.style.left = 0;
            background.style.top = 0;
            background.height = templateDimensions.height;
            background.width = templateDimensions.width;


            bgPosStretch.checked = true;
            bgPosCenter.checked = false;
        }
        else if (mode == 'Center')
        {
            background.height = background.naturalHeight;
            background.width = background.naturalWidth;

            if (background.width > templateDimensions.width ||
                background.height > templateDimensions.height)
            {
                if (background.width > templateDimensions.width)
                {
                    var ratio = templateDimensions.width/background.width;

                    background.width = templateDimensions.width;
                    background.height = background.height * ratio;
                    background.style.top = templateDimensions.height/2.0 - background.height/2.0;
                    background.style.left = 0;

                }

                if (background.height > templateDimensions.height)
                {
                    var ratio = templateDimensions.height/background.height;

                    background.height = templateDimensions.height;
                    background.height = background.height * ratio;

                    background.style.left = templateDimensions.width/2.0 - background.width/2.0;
                    baclground.style.top = 0;
                }
            }
            else
            {
                background.style.left = templateDimensions.width/2 - background.naturalWidth/2;
                background.style.top = templateDimensions.height/2 - background.naturalHeight/2;
            }


            bgPosStretch.checked = false;
            bgPosCenter.checked = true;

        }


    }

    function backgroundReceived() {
      Element.hide('loadingIcon')

      setBackgroundPos(backgroundPos);
    }

    function displayBackground(backgroundURL) {
        var newBackground = document.createElement('img');
        newBackground.id = 'background'
        newBackground.src = backgroundURL
        newBackground.style.position="absolute";
        newBackground.style.left = 0
        newBackground.style.top = 0
        newBackground.height = templateDimensions.height
        newBackground.width = templateDimensions.width
        newBackground.style.zIndex = 5
        newBackground.onload = backgroundReceived
        var template = $("templateDiv");
        template.appendChild(newBackground);
    }

    function removeBackground() {
      if (backgroundId != -1) {
        backgroundId = -1;
        Element.remove('background');
      }
    }

  </script>




<iframe id="uploadTarget" name="uploadTarget" src="" style="width:0px;height:0px;border:0" onload="sent()"></iframe>

<div style="width:100%%">
  <br/>

  <table class="groupTable" cellpadding="0">
    <tbody>
      <tr>
        <td class="groupTitle" colspan="6">%(titleMessage)s</td>
      </tr>
      <tr>
        <td class="titleCellTD">
          <span class="titleCellFormat">Name</span>
        </td>
        <td colspan="5">
          <input id="template name" size="50" name="Template Name">
        </td>
      </tr>
      <tr>
        <td class="titleCellTD">
          <span class="titleCellFormat">Background</span>
        </td>
        <form action="%(saveBackgroundURL)s" method="POST" ENCTYPE="multipart/form-data" onsubmit="sending()" target="uploadTarget">
        <td height="20px" NOWRAP align="left" colspan="3">
          <input name="file" size="58" type="file">
          <input class="btn" value="Send File" type="submit">
          <input class="btn" type="button" value="Remove background" onclick="removeBackground()">
        </td>
        <td width="100%%" align="left" colspan="4">
          <img id="loadingIcon" src=%(loadingIconURL)s width="20px" height="20px" style="display:none;">
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
           <input id="poster width" name="Poster Width" size="5">
        </td>
        <td class="titleCellTD" NOWRAP>
          <span class="titleCellFormat">Poster Height (cm)&nbsp;</span>
        </td>
        <td>
          <input id="poster height" name="Poster Height" size="5">
          <input class="btn" value="Change" type="button" onclick="changeTemplateSize()">
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

          <input name="Insert Template Element Button" class="btn" value="Insert" type="button" onclick="insertElement()">
          <input name="Delete Template Element Button" class="btn" value="Remove" type="button" onclick="removeElement()">

          <br/><br/>

          <select name="Template Elements List" id="elementList">
            %(selectOptions)s
          </select>

          <br/>
          <br/>

          Selection: <span id="selection text"></span>
          <br/><br/>

          Position:
          <br/>

          <table>
            <tbody>
              <tr>
                <td></td>
                <td align="center">
                  <input name="Move Template Element Top Button" class="btn" value="Top" type="button" onclick="moveTop()">
                </td>
                <td></td>
              </tr>
              <tr>
                <td align="center">
                  <input name="Move Template Element Left Button" class="btn" value="Left" type="button" onclick="moveLeft()">
                </td>
                <td align="center">
                  <input name="Move Template Element Center Button" class="btn" value="Center" type="button" onclick="moveCenter()">
                </td>
                <td align="center">
                  <input name="Move Template Element Right Button" class="btn" value="Right" type="button" onclick="moveRight()">
                </td>
              </tr>
              <tr>
                <td></td>
                <td align="center">
                  <input name="Move Template Element Bottom Button" class="btn" value="Bottom" type="button" onclick="moveBottom()">
                </td>
                <td></td>
              </tr>
              <tr>
            </tbody>
          </table>

          <input id="snap checkbox" type="checkbox" onclick="snapToGrid()"><label for="snap checkbox">Snap to grid</label>

        </td>

        <td></td>

        <td align="left" valign="bottom" height="22"> <!-- height of the horizontal ruler images -->
          <div id="horizontal ruler" style="position: relative; height: 5px; top: -6px;">
          </div>
        </td>
      </tr>

      <tr>
        <td valign="top" align="right" width="22"> <!-- width of the vertical ruler image -->
          <div id="vertical ruler" style="position: relative; width: 5px; left: -6px;">
          </div>
        </td>

        <td align="left" valign="top">
          <div id="templateDiv" style="width:525px;height:742px;position:relative;left:0px;top:0px">
            <table border="1" width="100%%" height="100%%" cellspacing="0" cellpadding="0">
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
          <select id='font selector' onChange="changeFont()" name="Template Element Font">
            <optgroup label="Normal Fonts">
              <option>Times New Roman</option>
              <option>Courier</option>
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

        <td width="100%%">
          <select id='color selector' name="Template Element Color" onchange="changeColor()">
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
          <select id='style selector' name="Template Element Style" onchange="changeStyle()">
            <option>Normal</option>
            <option>Bold</option>
            <option>Italic</option>
            <option>Bold &amp; Italic</option>
          </select>
        </td>

        <td class="titleCellTD">
          <span class="titleCellFormat">Size&nbsp;</span>
        </td>

        <td width="100%%">
          <select id='size selector' name="Template Element Size" onchange="changeSize()">
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
          <select id='alignment selector' name="Template Element Alignment" onChange="changeAlignment()">
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
        <td width="100%%">
          <input id="width field" size="5" name="Element Size">
          <input class="btn" value="Change" type="button" onclick="changeWidth()">
        </td>
      </tr>
      <tr>
        <td class="titleCellTD" NOWRAP>
          <span class="titleCellFormat">Text (for Fixed Text)&nbsp;</span>
        </td>
        <td>
          <input id="fixed text field" size="30" name="Element Size">
        </td>
        <td>
          <input class="btn" value="Change" type="button" onclick="changeText()">
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
        <td colspan="4" align="center" width="100%%">
          <input class="btn" name="Save Template Button" value="Save" type="button" onclick="save()">
          <input class="btn" name="Cancel Button" value="Cancel" type="button" onclick="location.href='%(cancelURL)s'">
        </td>
      </tr>
    </tbody>
  </table>

  <form name="hiddenform" action="%(saveTemplateURL)s" method="POST">
      <input name="templateId" value="%(templateId)s" type="hidden">
      <input id="templateData" name="templateData" type="hidden">
  </form>

<!--
  <table id='test' width="200" height="200" border="1" onclick="alert(Element.getDimensions(this).width);this.width = parseInt(this.width) + 10; return false">
    <tr><td></tr></td>
  </table>
-->

  <script type="text/javascript">

    // We load the template if we are editing a template
    if (%(editingTemplate)s) {
       var template = eval(%(templateData)s.unescapeHTML());
       $('template name').value = template[0];
       $('templateDiv').style.width = template[1].width;
       $('templateDiv').style.height = template[1].height;
       items = template[4];
       // We give the toHTML() method to each of the items
       items.each (function (item) {
         item.toHTML = Item.prototype.toHTML
       });
       templateDimensions = new Dimensions(template[1].width, template[1].height);
    } else {
       templateDimensions = new Dimensions(525,742); //put here the initial dimensions of templateDiv
    }

    previousTemplateDimensions = new Dimensions(0,0)

    $('poster width').value = templateDimensions.width / pixelsPerCm;
    $('poster height').value = templateDimensions.height / pixelsPerCm;

    // This function initialises the rulers
    updateRulers();

    // This function displays the items, if any have been loaded, on the screen
    displayItems()

    if (%(editingTemplate)s && %(hasBackground)s) {
       backgroundId = %(backgroundId)s
       backgroundPos = '%(backgroundPos)s'
       displayBackground("%(backgroundURL)s")
    }

  </script>

</div>
