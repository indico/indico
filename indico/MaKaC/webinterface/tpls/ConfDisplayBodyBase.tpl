<div class="toolbar header-aligned right">
    <%block name="toolbar"></%block>
</div>

<h2 class="page-title">
    <%block name="title"></%block>
</h2>

<div>
    ${ render_template('flashed_messages.html') }
    <%block name="content"></%block>
</div>
