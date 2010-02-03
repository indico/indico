<% import MaKaC %>
<% from MaKaC.search.base import ConferenceEntry %>

<% if categId: %>
  <% if categId == '0': %>
    <% name = "" %>
  <% end %>
  <% else: %>
    <% name = "in category" %>
  <% end %>
<% end %>
<% elif confId: %>
<% name = "Event" %>
<% end %>

<div class="container">
<% if searchingPublicWarning: %>
<div class="searchPublicWarning" style="float: right;" >
<%= _("Warning: since you are not logged in, only results from public events will appear.")%>
</div>
<% end %>

<h1 class="Search">Search <%= name %></h1>

<div class="topBar"><div class="content">

<div class="SearchDiv">

<div style="float: right; margin-top:10px;">
<span style="color:#777">Search powered by</span>
<a href="http://cdsware.cern.ch/invenio/"><img src="<%= systemIcon('invenio') %>" alt="CDS Invenio" title="<%= _("IndicoSearch is powered by CDS Invenio")%>" style="vertical-align: middle; border: 0px;" /></a>
</div>

<form method="GET" action="<%= urlHandlers.UHSearch.getURL() %>" style="width: 400px;">

<% if categId: %>
  <input type="hidden" name="categId" value="<%= categId %>"/>
<% end %>
<% if confId: %>
  <input type="hidden" name="confId" value="<%= confId %>"/>
<% end %>



<div>
  <input style="width: 300px; height:20px; font-size:17px; vertical-align: middle;" type="text" name="p" value="<%= p %>" />
  <input type="submit" value="<%= _('Search')%>" style="vertical-align: middle;"/>
</div>
<div style="padding-top: 4px;"><span id="advancedOptionsText"><span class='fakeLink' onclick='toogleAdvancedOptions()'><%=_("Show advanced options") %></span></span></div>
<div id="advancedOptions" style="overflow: hidden; visibility: hidden;">
    <table style="text-align: right;">
      <tr>
        <td><%= _("Search in") %>:</td>
        <td>
          <select class="UIFieldSpan" name="f">
    	<option value="" selected><%= _("Any Field")%></option>
    	<option value="title"><%= _("Title")%></option>
    	<option value="abstract"><%= _("Talk description/Abstract")%></option>
    	<option value="author"><%= _("Author/Speaker")%></option>
    	<option value="affiliation"><%= _("Affiliation")%></option>
    	<option value="fulltext"><%= _("Fulltext")%></option>
    	<option value="keyword"><%= _("Keyword")%></option>
          </select>
        </td>
      </tr>
      <tr>
        <td><%= _("Search for") %>:</td>
        <td>
          <select class="UIFieldSpan" name="collections">
    	<option value="Events"><%= _("Events")%></option>
    	<option value="Contributions"><%= _("Contributions")%></option>
    	<option value="" selected><%= _("Both (Events+Contributions)")%></option>
          </select>
        </td>
      </tr>
      <tr>
        <td><%= _("Start Date") %>:</td>
        <td id="startDatePlace">
        </td>
      </tr>
      <tr>
        <td><%= _("End Date") %>:</td>
        <td id="endDatePlace">
        </td>
      </tr>
      <tr>
        <td><%= _("Sort field") %>:</td>
        <td>
          <select class="UIFieldSpan" name="sortField" style="display: inline;">
            <option value=""><%= _("Latest first")%></option>
            <option value="title"><%= _("Title")%></option>
            <option value="author"><%= _("Author")%></option>
          </select>
        </td>
      </tr>
      <tr>
        <td><%= _("Sort order") %>:</td>
        <td>
          <select class="UIFieldSpan" name="sortOrder" style="display: inline;">
    	<option value="a"><%= _("Ascending")%></option>
    	<option value="d" selected><%= _("Descending")%></option>
          </select>
        </td>
      </tr>
    </table>
</div>



</form>

</div></div>

<% includeTpl('SearchNavigationForm', target = "Events", direction="Next") %>
<% includeTpl('SearchNavigationForm', target = "Contributions", direction="Next") %>
<% includeTpl('SearchNavigationForm', target = "Events", direction="Prev") %>
<% includeTpl('SearchNavigationForm', target = "Contributions", direction="Prev") %>

<% if p != '': %>
<h3 style="float:right">Hits: <%= numHits %></h3>
<% end %>

<div id="container">

<ul id="tabList">
<% if len(eventResults) > 0: %>
<li><a href="#events">Events</a></li>
<% end %>
<% if len(contribResults) > 0: %>
  <li><a href="#contribs">Contributions</a></li>
<% end %>
</ul>

<% if len(eventResults) > 0: %>
<div id="events">
  <% includeTpl('SearchNavigationBar', target = "Events", shortResult = evtShortResult) %>

  <ul class="searchResultList" style="list-style-type: none;">
    <% for result in eventResults: %>
    <% includeTpl('SearchResult', accessWrapper=self._aw, result=result) %>
    <% end %>
  </ul>
  <% includeTpl('SearchNavigationBar', target = "Events", shortResult = evtShortResult) %>
</div>
<% end %>

<% if len(contribResults) > 0: %>
<div id="contribs">
  <% includeTpl('SearchNavigationBar', target = "Contributions", shortResult = contShortResult) %>

  <ul class="searchResultList" style="list-style-type: none;">
    <% for result in contribResults: %>
    <% includeTpl('SearchResult', accessWrapper=self._aw, result=result) %>
    <% end %>
  </ul>
<% includeTpl('SearchNavigationBar', target = "Contributions", shortResult = contShortResult) %>
</div>
<% end %>

</div>


<% if len(contribResults) == 0 and len(eventResults) == 0 and p != '': %>
  <div style="margin-top: 20px; color: red;">No results found</div>
<% end %>
</div>
</div>

<script type="text/javascript">

var advancedOptionsSwitch = false;
var advancedOptions = $E("advancedOptions");
var advancedOptionsDivHeight=advancedOptions.dom.offsetHeight;
advancedOptions.dom.style.height = '0';
advancedOptions.dom.style.opacity = "0";

function toogleAdvancedOptions() {
    if (advancedOptionsSwitch) {
        IndicoUI.Effect.slide("advancedOptions", advancedOptionsDivHeight);
        $E("advancedOptionsText").dom.innerHTML = "<span class='fakeLink' onclick='toogleAdvancedOptions()'><%= _('Show advanced options') %></span>";
    }else {
        IndicoUI.Effect.slide("advancedOptions", advancedOptionsDivHeight);
        $E("advancedOptionsText").dom.innerHTML = "<span class='fakeLink' onclick='toogleAdvancedOptions()'><%= _('Hide advanced options') %></span>";
    }
    advancedOptionsSwitch = !advancedOptionsSwitch;
}

IndicoUI.executeOnLoad(function(){

<% if len(eventResults) > 0 or len(contribResults) > 0: %>
    var tabList = [];

<% if len(eventResults) > 0: %>
    tabList.push(['Events', $E('events')]);
<% end %>
<% if len(contribResults) > 0: %>
    tabList.push(['Contributions', $E('contribs')]);
<% end %>
    var tabCtrl = new TabWidget(tabList, $E('container').dom.clientWidth);
    $E('container').set(tabCtrl.draw());

<% end %>

var startDate = IndicoUI.Widgets.Generic.dateField(false, {name: 'startDate', style: {'width':'179px'}});
var endDate = IndicoUI.Widgets.Generic.dateField(false, {name: 'endDate', style: {'width':'179px'}});

$E('startDatePlace').set(startDate);
$E('endDatePlace').set(endDate);

startDate.set('<%= startDate %>');
endDate.set('<%= endDate %>');
});

</script>
