<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
    <div class="confDisplayInfoMessage">
        <div class="messageText">
            ${_("Sorry, but submission is not open yet. It will be available on " + start_date + ".")}
        </div>
    </div>
</%block>
