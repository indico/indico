<div class="layout-side-menu">
    <div class="menu-column"></div>
    <div class="content-column">
        <div class="banner">
            <div class="title">
                ${ _("Server Administration") }
            </div>
        </div>
    </div>
</div>
<div class="layout-side-menu">
    <div class="menu-column">
        ${ sideMenu }
    </div>
    <div class="content-column">
        ${ render_template('flashed_messages.html') }
        ${ body }
    </div>
</div>
