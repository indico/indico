
<form action=${participantSelectionAction} method="post" name="participantsForm">

<div id="list_options" class="toolbar" style="line-height: 3em;">
    <input type="text" id="filterSpeakers" value="" placeholder='${_("Search Name, Email &amp; Contributions")}' />

    <span class="not_important" style="font-size: 1.2em;">
      ${_('{0} speakers').format(participantNumber)}
    </span>


    <div id="actions" class="right group">
      <a class="icon-checkbox-checked button arrow left icon-only" aria-hidden="true" href="#" title="${_("Select")}" data-toggle="dropdown"></a>
      <ul class="dropdown">
        <li><a href="#" id="selectAll">All</a></li>
        <li><a href="#" id="selectNone">None</a></li>
      </ul>
      <a class="icon-mail button left icon-only" id="email_people" aria-hidden="true" href="#" title="${_("Email selected people")}"></a>
    </div>
</div>

<ul class="speaker_list clear">
    % for speaker in speakers:
    <li>
      <input type="checkbox" name="participants" value="${speaker['email']}" />

      % if speaker['email']:
        <a href="mailto:${speaker['email']}" class="name">${speaker['name']}</a>
      % else:
        <span class="name">${speaker['name']}</span>
      % endif

      <ul class="contributions">
        % for contribution in speaker['contributions']:
        <li><a href="${contribution['url']}">${contribution['title']}</a></li>
        % endfor
      </ul>
    </li>
    % endfor
</div>

</form>

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
    $('#actions').dropdown();
    $('#selectAll').click(function() {
        $('.speaker_list li:visible input').prop('checked', true);
    });

    $('#selectNone').click(function() {
        $('.speaker_list li:visible input').prop('checked', false);
    });

    $("#filterSpeakers").keyup(function() {
        filterEntries();
    });
});

</script>
