<div id="actionsToolbar" class="bs-alert alert-toolbar">
    <form action=${participantSelectionAction} method="post" name="participantsForm">
    <input type="text" id="filterSpeakers" value="" placeholder='${_("Search Name, Email &amp; Contributions")}' class="toolbar-search" /><input type="submit" class="bs-btn bs-btn-right" value="${_("Email Selected Speakers")}" name="sendEmails" />
    <div>
        ${_('Total Speakers')}: ${participantNumber}
    </div>
    <div style="padding-top:5px;">
        <span class="fakeLink" id="selectAllParticipants">${_('Select All')}</span> -
        <span class="fakeLink" id="selectNoParticipants">${_('Select None')}</span>
    </div>
    <div class="toolbar-clearer"></div>
</div>

<div>
    % for speaker in speakers:
    <div class="speakerEntry">
        <div class="speakerDetails">
            <input type="checkbox" name="participants" value="${speaker['email']}" />
            <span class="speakerName">
                ${speaker['name']}
            </span>
            <span class="speakerEmail">
                (${speaker['email']})
            </span>
        </div>
        <div class="speakerContributions">
            <ol>
            % for contribution in speaker['contributions']:
                <li><a href="${contribution['url']}">${contribution['title']}</a></li>
            % endfor
            </ol>
        </div>
    </div>
    % endfor
    </form>
</div>

<script type="text/javascript">

function filterEntries() {
    $(".speakerEntry").hide();
    var term = $("#filterSpeakers").attr('value');
    var items = $(".speakerContributions ol li a:contains('"+ term +"'), " +
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
        filterEntries();
    });
});

</script>