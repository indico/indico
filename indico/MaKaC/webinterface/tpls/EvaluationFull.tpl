<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
    <div class="confDisplayInfoMessage">
        <div class="messageText">${_("Maximum number of submissions reached.")}</div>
    </div>
</%block>