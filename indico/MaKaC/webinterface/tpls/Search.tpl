<% import MaKaC %>
<% from MaKaC.search.base import ConferenceEntry %>

% if categId:
  % if categId == '0':
    <% name = "" %>
  % else:
    <% name = "category" %>
  % endif
% elif confId:
<% name = "Event" %>
% endif

<div class="container">
% if searchingPublicWarning:
<div class="searchPublicWarning" style="float: right;" >
${ _("Warning: since you are not logged in, only results from public events will appear.")}
</div>
% endif

<h1 class="Search">Search ${ name }</h1>

<div class="topBar"><div class="content">

<div class="SearchDiv">

<div style="float: right; margin-top:10px;">
<span style="color:#777">Search powered by</span>
<a href="http://invenio-software.org"><img src="${ systemIcon('invenio') }" alt="CDS Invenio" title="${ _("IndicoSearch is powered by CDS Invenio")}" style="vertical-align: middle; border: 0px;" /></a>
</div>

<form method="GET" action="${ urlHandlers.UHSearch.getURL() }" style="width: 400px;">

% if categId:
  <input type="hidden" id="categId" name="categId" value="${ categId }"/>
% endif
% if confId:
  <input type="hidden" name="confId" value="${ confId }"/>
% endif


<div>
  <input style="width: 300px; height:20px; font-size:17px; vertical-align: middle;" type="text" name="p" value="${ p }" />
  <input type="submit" value="${ _('Search')}" style="vertical-align: middle;"/>
</div>

<div style="padding-top: 4px;"><span id="advancedOptionsText"><span class='fakeLink' onclick='toogleAdvancedOptions()'>${_("Show advanced options") }</span></span></div>
<div id="advancedOptions" style="overflow: hidden; visibility: hidden;">
    <table style="text-align: right;" id="advancedOptionsTable">
      <tr>
        <td>${ _("Search in") }:</td>
        <td>
          <select class="UIFieldSpan" name="f">
        <option value="" ${"selected" if f=="" else ""}>${ _("Any Field")}</option>
        <option value="title" ${"selected" if f=="title" else ""}>${ _("Title")}</option>
        <option value="abstract" ${"selected" if f=="abstract" else ""}>${ _("Talk description/Abstract")}</option>
        <option value="author" ${"selected" if f=="author" else ""}>${ _("Author/Speaker")}</option>
        <option value="affiliation" ${"selected" if f=="affiliation" else ""}>${ _("Affiliation")}</option>
        <option value="fulltext" ${"selected" if f=="fulltext" else ""}>${ _("Fulltext")}</option>
        <option value="keyword" ${"selected" if f=="keyword" else ""}>${ _("Keyword")}</option>
          </select>
        </td>
      </tr>
      <tr>
        <td>${ _("Search for") }:</td>
        <td>
          <select class="UIFieldSpan" name="collections">
        <option value="Events" ${"selected" if collections=="Events" else ""}>${ _("Events")}</option>
        <option value="Contributions" ${"selected" if collections=="Contributions" else ""}>${ _("Contributions")}</option>
        <option value="" ${"selected" if collections=="" else ""}>${ _("Both (Events+Contributions)")}</option>
          </select>
        </td>
      </tr>
      <tr>
        <td>${ _("Start Date") }:</td>
        <td id="startDatePlace">
        </td>
      </tr>
      <tr>
        <td>${ _("End Date") }:</td>
        <td id="endDatePlace">
        </td>
      </tr>
      <tr>
        <td>${ _("Sort field") }:</td>
        <td>
          <select class="UIFieldSpan" name="sortField" style="display: inline;">
            <option value="" ${"selected" if sortField=="" else ""}>${ _("Latest first")}</option>
            <option value="title" ${"selected" if sortField=="title" else ""}>${ _("Title")}</option>
            <option value="author" ${"selected" if sortField=="author" else ""}>${ _("Author")}</option>
          </select>
        </td>
      </tr>
      <tr>
        <td>${ _("Sort order") }:</td>
        <td>
          <select class="UIFieldSpan" name="sortOrder" style="display: inline;">
        <option value="a" ${"selected" if sortOrder=="a" else ""}>${ _("Ascending")}</option>
        <option value="d" ${"selected" if sortOrder=="d" else ""}>${ _("Descending")}</option>
          </select>
        </td>
      </tr>
    </table>
</div>



</form>

</div></div>

<%include file="SearchNavigationForm.tpl" args="target = 'Events', direction='Next'"/>
<%include file="SearchNavigationForm.tpl" args="target = 'Contributions', direction='Next'"/>
<%include file="SearchNavigationForm.tpl" args="target = 'Events', direction='Prev'"/>
<%include file="SearchNavigationForm.tpl" args="target = 'Contributions', direction='Prev'"/>

% if p != '':
<h3 style="float:right;margin:0px;">Hits: ${ numHits }</h3>
% endif

<div id="container" style="clear:both;">

% if len(eventResults) > 0:
<div id="events">
  <%include file="SearchNavigationBar.tpl" args="target = 'Events', shortResult = evtShortResult"/>

  <ul class="searchResultList">
    % for result in eventResults:
    <%include file="SearchResult.tpl" args="accessWrapper=self_._aw, result=result"/>
    % endfor
  </ul>
  <%include file="SearchNavigationBar.tpl" args="target = 'Events', shortResult = evtShortResult"/>
</div>
% endif

% if len(contribResults) > 0:
<div id="contribs">
  <%include file="SearchNavigationBar.tpl" args="target = 'Contributions', shortResult = contShortResult"/>

  <ul class="searchResultList">
    % for result in contribResults:
    <%include file="SearchResult.tpl" args="accessWrapper=self_._aw, result=result"/>
    % endfor
  </ul>
<%include file="SearchNavigationBar.tpl" args="target = 'Contributions', shortResult = contShortResult"/>
</div>
% endif

</div>


% if len(contribResults) == 0 and len(eventResults) == 0 and p != '':
  <div style="margin-top: 20px; color: red;">No results found</div>
% endif
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
        $E("advancedOptionsText").dom.innerHTML = "<span class='fakeLink' onclick='toogleAdvancedOptions()'>${ _('Show advanced options') }</span>";
    }else {
        IndicoUI.Effect.slide("advancedOptions", advancedOptionsDivHeight);
        $E("advancedOptionsText").dom.innerHTML = "<span class='fakeLink' onclick='toogleAdvancedOptions()'>${ _('Hide advanced options') }</span>";
    }
    advancedOptionsSwitch = !advancedOptionsSwitch;
}


$(function(){

% if len(eventResults) > 0 or len(contribResults) > 0:
    var tabList = [];

% if len(eventResults) > 0:
    tabList.push([$T('Events'), $E('events')]);
% endif
% if len(contribResults) > 0:
    tabList.push([$T('Contributions'), $E('contribs')]);
% endif
    var tabCtrl = new JTabWidget(tabList);
    $E('container').set(tabCtrl.draw());
    $('#container>div').css({"display":"table", "width":"100%"});

% endif

var startDate = IndicoUI.Widgets.Generic.dateField(false, {name: 'startDate', style: {'width':'157px'}});
var endDate = IndicoUI.Widgets.Generic.dateField(false, {name: 'endDate', style: {'width':'157px'}});

$E('startDatePlace').set(startDate);
$E('endDatePlace').set(endDate);

startDate.set('${ startDate }');
endDate.set('${ endDate }');
});
</script>
