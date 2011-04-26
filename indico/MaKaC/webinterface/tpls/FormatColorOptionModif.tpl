<form id="${ formatOption }Form" action=${ changeColorURL } method="post">

    <input id="colorTextField" size="7" type="text" value="${ colorCode }" name="colorCode">

    % if colorCode == "":
        <% colorPreview = "white" %>
        <% removeColorDisplay = "none" %>
    % else:
        <% colorPreview = colorCode %>
        <% removeColorDisplay = "inline" %>
    % endif

    <input name="colorpreview" type="text" style="background: ${ colorPreview }; border:1px solid black;width:20px;" DISABLED>


    <a href="" onClick="javascript:window.open('${ colorChartURL }','color','scrollbars=no,menubar=no,width=330,height=140');return false;">
        <img style="border:0px; vertical-align: middle" src="${ colorChartIcon }" alt="Select color">
    </a>&nbsp;&nbsp;
    <input type="submit" value="${ _("Apply color")}">
    <input type="submit" onclick="$E('${ formatOption }Form').dom.elements[0].value='';" value="${ _("Remove color")}" style="display: ${ removeColorDisplay };">

</form>
