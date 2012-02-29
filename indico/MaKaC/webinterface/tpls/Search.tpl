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


<div id="UISearch">
    <div id="searchControls">
        <div class="yellowButton searchButton" id="searchButton2">
            <input style="background-color: transparent;" class="button" type="submit" value="${ _('Search')}" onclick="javascript: return verifyForm();" id="searchSubmit"/>
        </div>
        <input style="background-color: transparent; margin-top: -1px;" type="text" id="searchText2" name="p" value="${ p }"/>
    </div>
</div>

<div style="padding-top: 4px;"><span id="advancedOptionsText"><span class='fakeLink' onclick='toogleAdvancedOptions()'>${_("Show advanced options") }</span></span></div>
<div id="advancedOptions" style="overflow: hidden; visibility: hidden;">
    <table style="text-align: right;" id="advancedOptionsTable">
      <tr>
        <td>${ _("Search in") }:</td>
        <td>
          <select class="UIFieldSpan" name="f">
        <option value="" selected>${ _("Any Field")}</option>
        <option value="title">${ _("Title")}</option>
        <option value="abstract">${ _("Talk description/Abstract")}</option>
        <option value="author">${ _("Author/Speaker")}</option>
        <option value="affiliation">${ _("Affiliation")}</option>
        <option value="fulltext">${ _("Fulltext")}</option>
        <option value="keyword">${ _("Keyword")}</option>
          </select>
        </td>
      </tr>
      <tr>
        <td>${ _("Search for") }:</td>
        <td>
          <select class="UIFieldSpan" name="collections">
        <option value="Events">${ _("Events")}</option>
        <option value="Contributions">${ _("Contributions")}</option>
        <option value="" selected>${ _("Both (Events+Contributions)")}</option>
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
            <option value="">${ _("Latest first")}</option>
            <option value="title">${ _("Title")}</option>
            <option value="author">${ _("Author")}</option>
          </select>
        </td>
      </tr>
      <tr>
        <td>${ _("Sort order") }:</td>
        <td>
          <select class="UIFieldSpan" name="sortOrder" style="display: inline;">
        <option value="a">${ _("Ascending")}</option>
        <option value="d" selected>${ _("Descending")}</option>
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


IndicoUI.executeOnLoad(function(){

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


if ($('#categId').attr('value')!=0){
    $('#searchText2').before('<div id="searchTag2" class="inCategory2">'+
            '<div id="cross2" class="cross2">x</div>'+
            '<div id="categorySearch2">${_("in %s") % categName}</div>'+
            '<div id="noCategorySearch2" style="display: none;">${_("Everywhere")}</div></div>​');
}
else{
    $('#searchText2').before('<div id="searchTag2" class="everywhere2">'+
            '<div id="cross2" class="cross2" style="display: none;">x</div>'+
            '<div id="categorySearch2" style="display: none;">${_("in %s") % categName}</div>'+
            '<div id="noCategorySearch2">${_("Everywhere")}</div></div>​');
}

$('#cross2').click(function() {
    $('#categorySearch2').fadeOut('fast');
    $('#cross2').fadeOut('fast');

     $('#searchTag2').animate({
        width: $('#noCategorySearch2').width(),
        opacity: 0.6
    }, 500);


    $('#categId').attr('value', 0);
    $('#searchTag2').attr('class', 'everywhere2');
    $('#noCategorySearch2').fadeIn('fast');

});
var animDone2=false;
$('.everywhere2').live('mouseenter', function() {
    $('#noCategorySearch2').addClass('hasFocus');
    setTimeout(function(){
        if ($('#noCategorySearch2').hasClass('hasFocus')){
            if (${categId}!=0){
                $('#noCategorySearch2').fadeOut('fast');

                    $('#searchTag2').animate({
                        width: $('#categorySearch2').width(),
                        opacity: 1
                    },500,'linear', function(){animDone2=true;});

                $('#searchTag2').attr('class', 'inCategoryOver2');
                $('#categorySearch2').fadeIn('fast');
            }
        }
    }, 200);

});

$('#noCategorySearch2').mouseleave(function() {
    $('#noCategorySearch2').removeClass('hasFocus');
});

$('#categorySearch2').mouseenter(function() {
    $('#noCategorySearch2').removeClass('hasFocus');
});

$('.inCategoryOver2').live('mouseleave', function() {
    $('#noCategorySearch2').removeClass('hasFocus');
    animDone2=false;
    setTimeout(function(){
        if(!$('#noCategorySearch2').hasClass('hasFocus')){
            if ($('#categId').attr('value')==0){
                $('#categorySearch2').fadeOut('fast');
                $('#cross2').fadeOut('fast');

                $('#searchTag2').animate({
                width: $('#noCategorySearch2').width(),
                opacity: 0.6
                },500);


                $('#searchTag2').attr('class', 'everywhere2');
                $('#noCategorySearch2').fadeIn('fast');
            }
        }
    }, 200);
});

$('#categorySearch2').click(function() {
    if($('#searchTag2').attr('class')=='inCategoryOver2' && animDone2==true){
        animDone2=false;
        $('#searchTag2').animate(
                {width: $('#categorySearch2').width()+$('#cross2').width()+6,
                 opacity: 1},
                 500,
                 'swing',
                 function(){
                     $('#cross2').fadeIn('fast');
                     }
                 );

        $('#searchTag2').attr('class', 'inCategory2');
        $('#categId').attr('value', ${categId});
    }
});

$('#noCategorySearch2').click(function() {
    if (navigator.platform.indexOf("iPad")!=-1 ||
        navigator.platform.indexOf("iPod")!=-1 ||
        navigator.platform.indexOf("iPhone")!=-1 ||
        navigator.userAgent.indexOf("Android")!=-1){
        if (${categId}!=0){
            $('#noCategorySearch2').fadeOut('fast');
            $('#categorySearch2').fadeIn('fast');
            $('#searchTag2').attr('class', 'inCategory');
            $('#categId').attr('value', ${categId});
            $('#searchTag2').animate(
                {width: $('#categorySearch2').width()+$('#cross2').width()+6,
                opacity: 1},
                500,
                'swing',
                function(){
                $('#cross2').fadeIn('fast');
                }
            );
        }
    }
});

$('.inCategoryOver2').live('mouseover', function(event) {
    $('.inCategoryOver2').qtip({
        content:'${_("Click to search inside %s." % categName)}',
        position:{
            at: 'bottom center',
            my: 'top center'
        },
        style: {
            classes: 'ui-tooltip-shadow'
        },
        events: {
            show: function(event, api) {
               if($('#searchTag2').attr('class')!='inCategoryOver2') {
                  try { event.preventDefault(); } catch(e) {}
               }
            }
         },
        show: {
            event: event.type,
            ready: true
         }
        }, event);
});




});

</script>
