<%page args="target=None, direction=None"/>
% if direction == 'Next':
  <% inc = 1 %>
% else:
  <% inc = -1 %>
% endif

% if target == 'Events':
  <% resList = eventResults %>
% else:
  <% resList =  contribResults %>
% endif


<form id="${ direction }Form${ target }" method="GET" action="${ urlHandlers.UHSearch.getURL()}">
  <input type="hidden" name="startDate" value="${ startDate }"/>
  <input type="hidden" name="endDate" value="${ endDate }"/>
  <input type="hidden" name="p" value="${ p }"/>
  <input type="hidden" name="f" value="${ f }"/>
  <input type="hidden" name="collections" value="${ target }"/>
  % if type(self_._rh._target) == MaKaC.conference.Category:
    <input type="hidden" name="categId" value="${ self_._rh._target.getId() }" />
  % elif type(self_._rh._target) == MaKaC.conference.Conference:
    <input type="hidden" name="confId" value="${ self_._rh._target.getId() }" />
  % endif
  % if len(resList) > 0:
    <input type="hidden" name="page" value="${ page + inc }" />
  % endif
    <input type="hidden" name="sortOrder" value="${ sortOrder }" />
</form>
