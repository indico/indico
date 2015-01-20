<form action=${convenerSelectionAction} method="post" id="convenersForm" name="convenersForm">

<div id="list_options" class="toolbar" style="line-height: 3em;">
  <input type="text" id="filterSpeakers" value="" placeholder="${_("Search Name, Email &amp; Sessions")}"/>

  <span class="text-not-important" style="font-size: 1.2em;">
    ${_('{0} conveners').format(convenerNumber)}
  </span>

  <div id="actions" class="right group">
    <a class="icon-checkbox-checked i-button arrow left icon-only" aria-hidden="true" href="#" title="${_("Select")}" data-toggle="dropdown"></a>
    <ul class="dropdown">
      <li><a href="#" id="selectAll">All</a></li>
      <li><a href="#" id="selectNone">None</a></li>
    </ul>
    <a class="icon-mail i-button left icon-only" id="email_people" aria-hidden="true" href="#" title="${_("Email selected people")}"></a>
  </div>

</div>


<ul class="speaker_list clear">
    % for convener in conveners:
    <li>
      <input type="checkbox" name="conveners" value="${convener['email']}" />
      % if convener['email']:
        <a href="mailto:${convener['email']}" class="name">${convener['name']}</a>
      % else:
        <span class="name">${convener['name']}</span>
      % endif
      <ul class="contributions">
          % for session in convener['sessions']:
          <li>
            ${session['title']} -
            <a href="${session['urlTimetable']}">
              ${_('timetable')}
            </a>
            % if session['urlSessionModif']:
              |
              <a href="${session['urlSessionModif']}">
                ${_('session')}
              </a>
            % endif
          </li>
          % endfor
        </ul>
    </li>
    % endfor
</ul>
</form>

<script type="text/javascript">

function verifyFilters() {
    $(".speaker_list > li").hide();
    var term = $("#filterSpeakers").val();
    var items = $('ul.contributions li, .speaker_list li .name').textContains(term);
    items.add($('.speaker_list li input').valueContains(term));
    items.closest('.speaker_list > li').show();
}

$(function() {
    $('#actions').dropdown();
    $('#selectAll').click(function() {
        $('.speaker_list li:visible input').prop('checked', true);
    });

    $('#selectNone').click(function() {
        $('.speaker_list li:visible input').prop('checked', false);
    });

    $("#filterSpeakers").keyup(function() {
        verifyFilters();
    });

    $('#email_people').click(function() {
        $('#convenersForm').submit();
        return false;
    });
});

</script>
