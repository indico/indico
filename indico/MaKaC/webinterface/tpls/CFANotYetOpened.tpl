<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
    <div class="info-message-box">
        <div class="message-text">
            ${_("Sorry, but submission is not open yet. It will be available on " + start_date + ".")}
        </div>
    </div>
</%block>
