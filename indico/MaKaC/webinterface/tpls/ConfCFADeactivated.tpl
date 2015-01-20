<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
    <div class="info-message-box">
        <div class="message-text">${_("Sorry, abstract submission is disabled for this conference.")}</div>
    </div>
</%block>
