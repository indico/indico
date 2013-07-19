<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
    <div class="info-message-box">
        <div class="message-text">
            % if is_modif: # easier to translate
                ${_("Sorry, but the deadline for abstract modification finished on {date}.".format(date=end_date))}
            % else:
                ${_("Sorry, but the deadline for abstract submission finished on {date}.".format(date=end_date))}
            % endif
        </div>
    </div>
</%block>
