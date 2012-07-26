<div id="speakerActions" class="bs-alert alert-toolbar">
    <form action=${convenerSelectionAction} method="post" name="convenersForm" target='_blank'>
    <input type="text" id="filterSpeakers" value="" placeholder='${_("Search Name, Email &amp; Sessions")}' class="toolbar-search" />
    <input type="submit" class="bs-btn bs-btn-right" value="${_("Email Selected Speakers")}" name="sendEmails" />
    <div>
        ${_('Total Conveners')}: ${convenerNumber}
    </div>
    <div style="padding-top:5px;">
        <span class="fakeLink" id="selectAllParticipants">${_('Select All')}</span> -
        <span class="fakeLink" id="selectNoParticipants">${_('Select None')}</span>
    </div>
    <div class="toolbar-clearer"></div>
</div>

<div>
    % for convener in conveners:
    <div class="speakerEntry">
        <div class="speakerDetails">
            <input type="checkbox" name="conveners" value="${convener['email']}" />
            <span class="speakerName">
                ${convener['name']}
            </span>
            <span class="speakerEmail">
                (${convener['email']})
            </span>
        </div>
        <div class="speakerContributions">
            <ol>
            % for session in convener['sessions']:
                <li>
                    ${session['title']} -
                    <a href="${session['urlTimetable']}">
                        ${_('Edit Timetable')}
                    </a>
                    % if session['urlSessionModif']:
                    | <a href="${session['urlSessionModif']}">
                        ${_('Edit Session')}
                    </a>
                    % endif
                </li>
            % endfor
            </ol>
        </div>
    </div>
    % endfor
    </form>
</div>

<script type="text/javascript">

function verifyFilters() {
    $(".speakerEntry").hide();
    var term = $("#filterSpeakers").attr('value');
    var items = $(".speakerContributions ol li:contains('"+ term +"'), " +
                  ".speakerEmail:contains('"+ term +"'), " +
                  ".speakerName:contains('"+ term +"')").closest('.speakerEntry');
    items.show();
};

$(document).ready(function() {
    $('#selectAllParticipants').click(function() {
        $('.speakerDetails:visible input').prop('checked', true);
    });

    $('#selectNoParticipants').click(function() {
        $('.speakerDetails input').prop('checked', false);
    });

    $("#filterSpeakers").keyup(function() {
        verifyFilters();
    });
});

</script>