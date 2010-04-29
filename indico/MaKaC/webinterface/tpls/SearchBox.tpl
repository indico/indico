<form method="get" action="%(searchAction)s" id="searchBoxForm" style="margin: 0px;">
<input type="hidden" id="searchCategId" name="categId" value="<%=categId%>"/>
<div id="UISearchBox">
    <div id="searchControls">
        <div class="yellowButton searchButton">
            <input style="background-color: transparent;" class="button" type="submit" value="<%= _('Search')%>" onclick="javascript: return verifyForm();" id="searchSubmit"/>
        </div>
	<div style="background: white; padding: 2px;">
	  <div id="yoo" class="<%= moreOptionsClass %>" onclick="javascript:return expandMenu(this);"></div>
	  <input style="background-color: transparent; margin-top: -1px;" type="text" id="searchText" name="p" />
    	</div>
    </div>

	<div id="extraOptions">
        <div id="advancedOptionsLabel"><%= _("Advanced options")%></div>
        <table>
            <tr>
                <td style="text-align: right;"><%= _("Search in")%></td>
                <td>
    				<select name="f">
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
                <td style="text-align: right;"><%= _("Search for")%></td>
                <td>
                    <select name="collections">
		      <option value="Events">Events</option>
		      <option value="Contributions">Contributions</option>
		      <option value="" selected>Both (Events+Contributions)</option>
                    </select>
                </td>
            </tr>
            <tr>
                <td style="text-align: right;"><%= _("Start Date")%></td>
                <td>
                    <span id="startDatePlaceBox">
                    </span>
                </td>
            </tr>
            <tr>
                <td style="text-align: right;"><%= _("End Date")%></td>
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
});
</script>
