<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
    <div class="info-message-box">
        <div class="message-text">${_("Sorry, but the evaluation is disabled for this event.")}</div>
    </div>
</%block>
