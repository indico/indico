<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
    <div class="info-message-box">
        <div class="message-text">${_("Maximum number of submissions reached.")}</div>
    </div>
</%block>