<form id="<%= formatOption %>Form" action=%(changeColorURL)s method="post">

    <input id="colorTextField" size="7" type="text" value="%(colorCode)s" name="colorCode">
    
    <% if colorCode == "": %>
        <% colorPreview = "white" %>
        <% removeColorDisplay = "none" %>
    <% end %>
    <% else: %>
        <% colorPreview = colorCode %>
        <% removeColorDisplay = "inline" %>
    <% end %>

    <input name="colorpreview" type="text" style="background: %(colorPreview)s; border:1px solid black;width:20px;" DISABLED>

    
    <a href="" onClick="javascript:window.open('%(colorChartURL)s','color','scrollbars=no,menubar=no,width=330,height=140');return false;">
        <img style="border:0px; vertical-align: middle" src="%(colorChartIcon)s" alt="Select color">
    </a>&nbsp;&nbsp;
    <input type="submit" value="<%= _("Apply color")%>">
    <input type="submit" onclick="$E('<%= formatOption %>Form').dom.elements[0].value='';" value="<%= _("Remove color")%>" style="display: <%= removeColorDisplay %>;">

</form>