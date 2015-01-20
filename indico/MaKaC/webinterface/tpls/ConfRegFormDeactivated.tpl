<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
    <div class="info-message-box">
        <div class="message-text">
            ${_("Sorry, the registration form is disabled for this conference.")}
        </div>
    </div>
</%block>