<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
    <div class="info-message-box">
        <div class="message-text">
            ${msg}
            <ul>
                <li>${_("Start date")}: ${startDate}</li>
                <li>${_("End date")}: ${endDate}</li>
            </ul>
        </div>
    </div>
</%block>