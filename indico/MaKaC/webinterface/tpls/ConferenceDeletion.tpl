<%inherit file="Confirmation.tpl"/>

<%block name="args">
  %for event in eventList:
    <input type="hidden" name="selectedConf" value="${event.getId()}" />
  %endfor
</%block>

<%block name="challenge">
  ${_('Are you sure that you want to delete the following events?')}
</%block>

<%block name="target">
  <ul class='categ-list'>
  %for event in eventList:
    <%
        start_date = formatDateTime(event.getAdjustedStartDate(), format="dd MMMM yyyy")
        end_date = formatDateTime(event.getAdjustedEndDate(), format="dd MMMM yyyy")
        date = "{0} - {1}".format(start_date, end_date) if start_date != end_date else start_date
    %>
    <li><span class="event-title">${event.getTitle()}</span>: <span class="event-date">${date}</span></li>
  %endfor
  </ul>
</%block>

<%block name="subtext">
  ${_("Note that ALL the content therein will be deleted as well")}
</%block>
