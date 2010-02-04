<li class="<% if type(result) == ConferenceEntry: %>searchResultEvent<% end %>
  <% else: %>searchResultContribution<% end %>">
      <% if result.getTitle(): %>
      <a class="searchResultTitle" href="<%= result.getURL().replace('%','%%') %>"><%= result.getTitle() %></a>
      <% end %>
      <% if result.getStartDate(accessWrapper): %>
    <small style="display: block;"><%= result.getStartDate(accessWrapper).strftime("%Y-%m-%d %H:%M:%S (%Z)") %></small>
    <% end %>

    <ul class="authorList">
  <% for author in result.getAuthors(): %>
  <li
      <% if author == result.getAuthors()[-1]: %>
      class="last"
	<% end %>
	><%= author.getName() %> <small>(<%= author.getRole() %>
	<% if author.getAffiliation(): %>
	, <%= author.getAffiliation() %>
	<% end %>)</small>
    </li>
    <% end %>
  </ul>

<%!
if result.getDescription() != None:
    fullDesc = result.getDescription()
    entryDesc = truncateTitle(result.getDescription(), maxSize=100)
else:
    fullDesc = entryDesc = ''
 %>

  <div class="searchResultDescription">
    <%= entryDesc %>

    <% if len(entryDesc) < len(fullDesc): %>
      <a href="#" class="searchResultLink" onclick="IndicoUI.Effect.appear($E('desc<%= result.getCompoundId() %>')); $E(this).getParent().getParent().remove($E(this).getParent()); return false;" style="margin-bottom: 10px;">more</a>
    <% end %>
  </div>

  <div id='desc<%= result.getCompoundId() %>' class="searchResultDescription" style="display: none;">
    <%= fullDesc %>
  </div>

  <ul class="nobulletsListInline" style="margin-top: 5px; margin-left: 20px;">
    <% for material in result.getMaterials(): %>
    <li><a class="searchResultLink" href="<%= material[0] %>"><%= material[1] %></a></li>
    <% end %>
  </ul>
</li>
