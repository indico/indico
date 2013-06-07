<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
    <div class="confDisplayInfoMessage">
        <div class="messageText">
            ${_("Sorry, but the deadline for abstract submission and modification finished on " + end_date + ".")}
        </div>
    </div>
</%block>
