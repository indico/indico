<form method="get" action="${ searchAction }" id="searchBoxForm" style="margin: 0px;">
<input type="hidden" id="searchCategId" name="categId" value="${categId}"/>
<div id="UISearchBox">
    <div id="searchControls">
        <div class="yellowButton searchButton">
            <input style="background-color: transparent;" class="button" type="submit" value="${ _('Search')}" onclick="javascript: return verifyForm();" id="searchSubmit"/>
        </div>
        <div id="yoo" class="${ moreOptionsClass }" onclick="javascript:return expandMenu(this);" on></div>
        <input style="background-color: transparent; margin-top: -1px;" type="text" id="searchText" name="p" />
</div>

    <div id="extraOptions">
        <div id="advancedOptionsLabel">${ _("Advanced options")}</div>
        <table id="extraOptionsTable">
        <tr>
                <td style="text-align: right;">${ _("Search in")}</td>
                <td>
                    <select name="f">
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
                <td style="text-align: right;">${ _("Search for")}</td>
                <td>
                    <select name="collections">
              <option value="Events">Events</option>
              <option value="Contributions">Contributions</option>
              <option value="" selected>Both (Events+Contributions)</option>
                    </select>
                </td>
            </tr>
            <tr>
                <td style="text-align: right;">${ _("Start Date")}</td>
                <td>
                    <span id="startDatePlaceBox">
                    </span>
                </td>
            </tr>
            <tr>
                <td style="text-align: right;">${ _("End Date")}</td>
                <td>
                    <span id="endDatePlaceBox">
                    </span>
                </td>
            </tr>
        </table>
    </div>
</div>
</form>

<script type="text/javascript">

function expandMenu(domElem)
{
    var elem = new XElement(domElem);

    if(!exists(elem.dom.extraShown))
    {
        var controls = searchControls;

        IndicoUI.Effect.appear(extraOptions, 'block');
        elem.dom.extraShown=true;
        resetForm();
    }
    else
    {
        IndicoUI.Effect.disappear(extraOptions)
        elem.dom.extraShown=null;
        resetForm();

    }
    return false;
}



function resetForm()
{
    // reset all the fields, except the phrase
    var text = $E('searchText').dom.value;
    $E('searchBoxForm').dom.reset();
    $E('searchText').dom.value = text;

}

function verifyForm()
{
    if ((startDateBox.get() && !startDateBox.processDate()) || (endDateBox.get() && !endDateBox.processDate()))
    {
        return false;
    }
    else
    {
        return true;
    }
}



var startDateBox = IndicoUI.Widgets.Generic.dateField(null, {name: 'startDate'});
var endDateBox = IndicoUI.Widgets.Generic.dateField(null, {name: 'endDate'});

var searchControls = $E('searchControls');
var extraOptions = $E('extraOptions');

var intelligentSearchBox = new IntelligentSearchBox({name: 'p', id: 'searchText',
                                 style: {backgroundColor: 'transparent', outline: 'none', marginTop: '-1px'}
                 }, $E('UISearchBox'), $E('searchSubmit'));

IndicoUI.executeOnLoad(function(){
  $E('startDatePlaceBox').set(startDateBox);
  $E('endDatePlaceBox').set(endDateBox);
  $E('searchText').replaceWith(
         intelligentSearchBox.draw()
     );

  if ($('#searchCategId').attr('value')!=0){
      $('#yoo').after('<div id="searchTag" class="inCategory">'+
              '<div id="cross" class="cross">x</div>'+
              '<div id="categorySearch">${_("in %s") % categName}</div>'+
              '<div id="noCategorySearch" style="display: none;">${_("Everywhere")}</div></div>​');
  }
  else{
      $('#yoo').after('<div id="searchTag" class="everywhere">'+
              '<div id="cross" class="cross" style="display: none;">x</div>'+
              '<div id="categorySearch" style="display: none;">${_("in %s") % categName}</div>'+
              '<div id="noCategorySearch">${_("Everywhere")}</div></div>​');
  }

  $('#cross').click(function() {
      $('#categorySearch').fadeOut('fast');
      $('#cross').fadeOut('fast');

       $('#searchTag').animate({
          width: $('#noCategorySearch').width(),
          opacity: 0.6
      }, 500);


      $('#searchCategId').attr('value', 0);
      $('#searchTag').attr('class', 'everywhere');
      $('#noCategorySearch').fadeIn('fast');

  });
var animDone=false;
  $('.everywhere').live('mouseenter', function() {
      $('#noCategorySearch').addClass('hasFocus');
      setTimeout(function(){
          if ($('#noCategorySearch').hasClass('hasFocus')){
              if (${categId}!=0){
                  $('#noCategorySearch').fadeOut('fast');

	                  $('#searchTag').animate({
	                      width: $('#categorySearch').width(),
	                      opacity: 1
	                  },500,'linear',
	                  function(){animDone=true;});

                  $('#searchTag').attr('class', 'inCategoryOver');
                  $('#categorySearch').fadeIn('fast');
              }
          }
      }, 200);

  });

  $('#noCategorySearch').click(function() {
      if (navigator.platform.indexOf("iPad")!=-1 ||
          navigator.platform.indexOf("iPod")!=-1 ||
          navigator.platform.indexOf("iPhone")!=-1 ||
          navigator.userAgent.indexOf("Android")!=-1){
          if (${categId}!=0){
              $('#noCategorySearch').fadeOut('fast');
              $('#categorySearch').fadeIn('fast');
              $('#searchTag').attr('class', 'inCategory');
              $('#searchCategId').attr('value', ${categId});
              $('#searchTag').animate(
                  {width: $('#categorySearch').width()+$('#cross').width()+6,
                  opacity: 1},
                  500,
                  'swing',
                  function(){
                  $('#cross').fadeIn('fast');
                  }
              );
          }
      }
  });


  $('#noCategorySearch').mouseleave(function() {
      $('#noCategorySearch').removeClass('hasFocus');
  });

  $('#categorySearch').mouseenter(function() {
      $('#noCategorySearch').removeClass('hasFocus');
  });

  $('.inCategoryOver').live('mouseleave', function() {
      $('#noCategorySearch').removeClass('hasFocus');
      animDone=false;
      setTimeout(function(){
          if(!$('#noCategorySearch').hasClass('hasFocus')){
              if ($('#searchCategId').attr('value')==0){
                  $('#categorySearch').fadeOut('fast');
                  $('#cross').fadeOut('fast');

                  $('#searchTag').animate({
                  width: $('#noCategorySearch').width(),
                  opacity: 0.6
                  },500);


                  $('#searchTag').attr('class', 'everywhere');
                  $('#noCategorySearch').fadeIn('fast');
              }
          }
      }, 200);
  });

  $('.inCategoryOver').live('click',function() {
          if($('#searchTag').attr('class')=='inCategoryOver' && animDone==true){
          animDone=false;
          $('#searchTag').animate(
                  {width: $('#categorySearch').width()+$('#cross').width()+6,
                   opacity: 1},
                   500,
                   'swing',
                   function(){
                       $('#cross').fadeIn('fast');
                       justClicked = false;
                       }
                   );

          $('#searchTag').attr('class', 'inCategory');
          $('#searchCategId').attr('value', ${categId});
          }
  });

  $('.inCategoryOver').live('mouseover', function(event) {
      $('.inCategoryOver').qtip({
          content: '${_("Click to search inside %s.") % categName}',
          position:{
              at: 'bottom center',
              my: 'top center'
          },
          style: {
              classes: 'ui-tooltip-shadow'
          },
          events: {
              show: function(event, api) {
                 if($('#searchTag').attr('class')!='inCategoryOver') {
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
