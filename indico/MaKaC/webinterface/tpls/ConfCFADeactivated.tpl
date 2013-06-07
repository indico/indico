<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
    <div class="confDisplayInfoMessage">
        <div class="messageText">${_("Sorry, abstract submission is disabled for this conference.")}</div>
    </div>
</%block>
