<%
    import re
    somethingVisible = False
%>

<div class="sideBar sideMenu ${"managementSideMenu" if sideMenuType != "basic" else ""}">
    % if sideMenuType != "basic":
        <div class="corner"></div>
    % endif

    <div class="content">
        ${ render_template('side_menu.html', menu=menu) }
    </div>
</div>
