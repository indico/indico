
<script type="text/javascript">
// portable (?) menu package originally developped for the CERN public pages
// by Yves Perrin / EP

var menudivs = {};


function checkwhere(e) {
    var cursor = getMousePointerCoordinates(e);
    var mouseY = cursor.y;
    var mouseX = cursor.x;

    for(var menuKey in menudivs) {
        if (menudivs[menuKey].menuOn && !(menudivs[menuKey].onAnchor)) {

        if (!((mouseX >= menudivs[menuKey].anchorLeft) && (mouseX <= (menudivs[menuKey].anchorLeft+menudivs[menuKey].menuWidth))
            && (mouseY >= menudivs[menuKey].anchorTop) && (mouseY <= (menudivs[menuKey].anchorTop+menudivs[menuKey].anchorHeight+menudivs[menuKey].menuHeight)))
            ) {
            hideMenu(menudivs[menuKey].id);
        }
        }
    }
}

function getAnchorLocation(menuId) {
    var pos = $E(menudivs[menuId].anchorId).getAbsolutePosition();
    menudivs[menuId].anchorLeft = pos.x;
    menudivs[menuId].anchorTop  = pos.y;
}

function getMenuZone(menuId) {  // two rectangles in which the menu should be shown.
    var menuLayer = $E(menuId).dom;
    menudivs[menuId].menuWidth  = parseInt(menuLayer.offsetWidth);
    menudivs[menuId].menuHeight = parseInt(menuLayer.offsetHeight);
    var anchor = $E(menudivs[menuId].anchorId).dom;
    menudivs[menuId].anchorWidth  = parseInt(anchor.offsetWidth);
    menudivs[menuId].anchorHeight = parseInt(anchor.offsetHeight);
}

function setOnAnchor(menuId) {
    closeAll();
    getAnchorLocation(menuId);
    getMenuZone(menuId);
    menudivs[menuId].menuOn = true;
    menudivs[menuId].onAnchor = true;
    showMenu(menuId);
}

function clearOnAnchor(menuId) {
  menudivs[menuId].onAnchor = false;
}

function closeAll() {
    for(var menuKey in menudivs) {
        hideMenu(menudivs[menuKey].id);
    }
}

function showMenu(menuId) {
    var div = $E(menuId).dom;
    div.style.left = pixels(menudivs[menuId].anchorLeft);
    div.style.top  = pixels(menudivs[menuId].anchorTop + menudivs[menuId].anchorHeight);
    div.style.visibility = 'visible';

    menudivs[menuId].menuOn = true;
}

function hideMenu(menuId) {
    $E(menuId).dom.style.visibility = 'hidden';
    menudivs[menuId].menuOn = false;
}

document.onmousemove = checkwhere;
if(document.captureEvents) {document.captureEvents(Event.MOUSEMOVE);}

</script>





<div class="calendarContainer container">
    <div class="categoryHeader">
        <ul>
            <li><a href="${ categDisplayURL }">${ _("Go back to category page") }</a></li>
        </ul>
        <h1 class="categoryTitle">
            ${ categoryTitle | remove_tags }&nbsp;
            <span style="font-style: italic; font-size: 0.8em;">(${ _("calendar overview") })</span>
        </h1>
    </div>

    <table width="100%"><tbody>
    <tr><td width="330" valign="top">

    <div class="sideBar clearfix" style="margin-top: 30px; float: none; width: 320px;">
        <div class="leftCorner"></div>
        <div class="rightCorner"></div>
        <div class="content clearfix">

            <h1>${ _("Options") }</h1>
                <form action="${ changeMonthsURL }" method="GET" id="calendarOptionsForm">
                <table style="margin: 10px 0 10px 20px; padding: 0; border: none;">
                <tbody>
                    ${ locatorNoMonth }
                    <tr>
                        <td>${ _("Number of months")}:<td>
                        <td>
                            <select name="months" style="min-width: 50px;">
                                <option>1</option>
                                <option>2</option>
                                <option>3</option>
                                <option>4</option>
                                <option>5</option>
                                <option>6</option>
                                <option>7</option>
                                <option>8</option>
                                <option>9</option>
                                <option>10</option>
                                <option>11</option>
                                <option>12</option>
                            </select>
                        </td>
                    </tr>
                    <tr>
                        <td>${ _("Starting month")}:<td>
                        <td nowrap="nowrap">
                            <select name="month" style="min-width: 50px;">
                                <option>1</option>
                                <option>2</option>
                                <option>3</option>
                                <option>4</option>
                                <option>5</option>
                                <option>6</option>
                                <option>7</option>
                                <option>8</option>
                                <option>9</option>
                                <option>10</option>
                                <option>11</option>
                                <option>12</option>
                            </select>
                            <select name="year" style="min-width: 50px;">
                                % for year in reversed(range(currentYear - 10, currentYear + 1)):
                                    <option>${year}</option>
                                % endfor
                            </select>
                        </td>
                    </tr>
                    <tr>
                        <td nowrap="nowrap">${ _("Number of columns")}:<td>
                        <td>
                            <select name="columns" style="min-width: 50px;">
                                <option>1</option>
                                <option>2</option>
                                <option>3</option>
                                <option>4</option>
                                <option>5</option>
                                <option>6</option>
                            </select>
                        </td>
                    </tr>
                  </tbody>
                </table>

                <div style="text-align: center; margin-bottom: 20px;">
                    <input type="submit" class="btn" value="${ _("apply")}">
                </div>
                </form>
                <script type="text/javascript">

                var calendarOptionsForm = $E("calendarOptionsForm");

                calendarOptionsForm.dom.months.selectedIndex = ${selectedmonths} - 1;
                calendarOptionsForm.dom.columns.selectedIndex = ${selectedcolumns} - 1;
                calendarOptionsForm.dom.month.selectedIndex = ${selectedmonth} - 1;
                calendarOptionsForm.dom.year.selectedIndex=  ${currentYear - selectedyear};

                </script>


            <h1>${ _("Color legend") }</h1>
            <div class="calendarColorLegend clearfix">
                ${ legend }
                <div>
                    <form action="${ selCategsURL }" method="POST" style="margin-top: 10px;">
                        ${ locator }
                        <input type="submit" class="btn" value="${ _("change")}">
                    </form>
                </div>
            </div>

        </div>
    </div>
    </td>
    <td valign="top">
    <div style="margin-top: 20px; margin-left: 30px;">
        <table cellspacing="10" align="center" width="100%">
            ${ calendar }
        </table>
    </div>
    </td>
    </tr>
    </tbody></table>
</div>
