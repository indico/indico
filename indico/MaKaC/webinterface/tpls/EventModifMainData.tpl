<%!

# maybe all of this should be moved to the W* class?

from MaKaC.fossils.conference import IConferenceMinimalFossil
import MaKaC.webinterface.webFactoryRegistry as webFactoryRegistry
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.displayMgr as displayMgr
from xml.sax.saxutils import escape

wr = webFactoryRegistry.WebFactoryRegistry()
typeList = { "conference" : "conference" }
for fact in wr.getFactoryList():
    val = fact.getId()

    if val == 'simple_event':
        val = 'lecture'

    typeList[fact.getId()] = val

visibilityList = {}
topcat = confObj.getOwnerList()[0]
level = 0
visibilityList[0] = 'Nowhere'
while topcat:
    level += 1
    if topcat.getId() != "0":
        from MaKaC.common.TemplateExec import truncateTitle
        visibilityList[level] = truncateTitle(topcat.getName(), 50)
    topcat = topcat.getOwner()
visibilityList[999] = 'Everywhere'

numRows = 11


favoriteRooms = confObj.getFavoriteRooms();

%>
<div class="groupTitle"><%= _("General Settings")%></div>

<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat"><%= _("Title")%></span>
    </td>
    <td class="blacktext" style="width:100%">
        <span id="inPlaceEditTitle"><%=title %></span>
    </td>
    <td rowspan="<%=numRows%>" style="vertical-align: bottom;">
        <form action=<%= dataModificationURL %> method="post">
            <input type="submit" class="btn" value="modify"/>
        </form>
    </td>
</tr>
<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat"><%= _("Description")%></span>
    </td>
    <td>
        <div class="blacktext" id="inPlaceEditDescription"><%=description %></div>
    </td>
</tr>
<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat"><%= _("Place")%></span>
    </td>
    <td class="blacktext" id="inPlaceEditLocation">
        <strong><%= _("Location:")%> </strong>
        <span id="inPlaceEditLocationName"><%=locationName %></span>
        <br/>
        <strong><%= _("Address:")%> </strong>
        <span id="inPlaceEditLocationAddress"><%=locationAddress %></span>
        <br/>
        <strong><%= _("Room:")%> </strong>
        <span id="inPlaceEditLocationRoom"><%=locationRoom %></span>
        <div id="inPlaceEditLocation_Menu">
        </div>
    </td>
</tr>
<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat"><%= _("Start/End date")%></span>
    </td>
    <td class="blacktext">
        <span id="inPlaceEditStartEndDate"><%=startDate %> <strong>to</strong> <%= endDate %></span>
    </td>
</tr>
<!-- Fermi timezone awareness -->
<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat"><%= _("Timezone")%></span>
    </td>
    <td class="blacktext">
        <%=timezone%>
    </td>
</tr>
<!-- Fermi timezone awareness(end) -->
<% if evtType == 'conference':%>
<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat"><%= _("Additional info")%></span>
    </td>
    <td class="blacktext">
        <span id="inPlaceEditAdditionalInfo"><%=contactInfo%></span>
    </td>
</tr>
<%end%>
<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat"><%= _("Support") %></span>
    </td>
    <td class="blacktext">
        <span id="inPlaceEditSupport"><%= supportEmail %></span>
    </td>
</tr>
<% if evtType == 'lecture':%>
<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat"><%= _("Organisers")%></span>
    </td>
    <td class="blacktext">
        <span id="inPlaceEditOrganiserText"><%=confObj.getOrgText() %></span>
    </td>
</tr>
<% end %>
<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat"><%= _("Default style")%></span>
    </td>
    <td class="blacktext">
        <span id="inPlaceEditDefaultStyle"><%=defaultStyle %></span>
    </td>
</tr>
<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat"><%= _("Visibility")%></span>
    </td>
    <td class="blacktext">
        <span id="inPlaceEditVisibility"><%=visibility %></span>
    </td>
</tr>
<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat"><%= _("Event type")%></span>
    </td>
    <td class="blacktext">
        <span id="inPlaceEditType"><%=eventType %></span>
    </td>
</tr>
<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat"><%= _("Keywords")%></span>
    </td>
    <td class="blacktext">
        <%if keywords: %><pre><%= keywords %></pre>
        <%end %>
    </td>
</tr>

<tr>
    <% if Config.getInstance().getShortEventURL() != "": %>
      <td class="dataCaptionTD">
        <span class="dataCaptionFormat"><%= _("Short display URL")%></span>
      </td>
      <% if shortURL == "" : %>
        <td class="blacktext"><em><%= _("There is not any short url yet. Click \"Modify\" to setup.")%></em></td>
      <% end %>
      <% else : %>
      <td class="blacktext"><%=shortURL%></td>
      <% end %>
    <% end %>
</tr>


<tr>
    <td colspan="3" class="horizontalLine">
        &nbsp;
    </td>
</tr>
<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat"><%if evtType == 'lecture': %> <%= _("Speakers")%><%end %><%else: %> <%= _("Chairpersons")%><%end %></span>
    </td>
    <td colspan="2">
        <table width="100%">
            <tr>
                <td class="blacktext" style="width: 100%">
                    <form action=<%= remChairsURL %> method="post">
                        <input type="hidden" name="selChair" value="" />
                        <ul class="UIPeopleList">
                            <% for chair in chairs: %>
                                <li class="UIPerson">
                                    <a href="<%= urlHandlers.UHConfModChairEdit.getURL(chair) %>" class="nameLink">
                                        <%= escape (chair.getFullName()) %>
                                    </a>
                                    <input type="image" class="UIRowButton2" onclick="removeItem(<%=chair.getId()%>, this.form);return false;"  title="<%= _("Remove this person from the list")%>" src="<%= systemIcon("remove") %>" />
                                </li>
                            <% end %>
                        </ul>
                    </form>
                </td>
                <td>
                    <table>
                        <tr>
                            <td>
                                <form action=<%= newChairURL %> method="POST">
                                    <input type="submit" class="btn" value="new">
                                </form>
                            </td>
                            <td>
                                <form action=<%= searchChairURL %> method="POST">
                                    <input type="submit" class="btn" value="search">
                                </form>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </td>
</tr>
<tr>
    <td colspan="3" class="horizontalLine">&nbsp;</td>
</tr>

<script type="text/javascript">
function removeItem(number, form)
{
    form.selChair.value = number;
    form.submit();
}

var confFossile = <%= jsonEncode(confObj.fossilize(IConferenceMinimalFossil, tz=confObj.getTimezone())) %>;

<%= macros.genericField(macros.FIELD_TEXT, 'inPlaceEditTitle', 'event.main.changeTitle', {'conference': "%s"%conferenceId}, preCache=True, rh=self._rh) %>

<% dMgr = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(confObj) %>

$E('inPlaceEditSupport').set(new SupportEditWidget('event.main.changeSupport', <%= jsonEncode({'conference': "%s"%conferenceId}) %>, {'caption': "<%= dMgr.getSupportEmailCaption() %>", 'email': confFossile.supportEmail}).draw());

<% if evtType == 'lecture':%>
    <%= macros.genericField(macros.FIELD_TEXT, 'inPlaceEditOrganiserText', 'event.main.changeOrganiserText', {'conference': "%s"%conferenceId}, preCache=True, rh=self._rh) %>
<% end %>

<%  from MaKaC.common import info %>

<%= macros.genericField(macros.FIELD_SELECT, 'inPlaceEditDefaultStyle', 'event.main.changeDefaultStyle', {'conference': "%s"%conferenceId}, preCache=True, rh=self._rh, options=info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager().getStylesheetDictForEventType(confObj.getType())) %>

<%= macros.genericField(macros.FIELD_SELECT, 'inPlaceEditVisibility', 'event.main.changeVisibility', {'conference': "%s"%conferenceId}, preCache=True, rh=self._rh, options=visibilityList) %>

<%= macros.genericField(macros.FIELD_SELECT, 'inPlaceEditType', 'event.main.changeType', {'conference': "%s"%conferenceId}, preCache=True, rh=self._rh, options=typeList) %>

$E('inPlaceEditStartEndDate').set(new StartEndDateWidget('event.main.changeDates', <%= jsonEncode({'conference': "%s"%conferenceId}) %>, {'startDate': confFossile.startDate, 'endDate': confFossile.endDate}).draw());

$E('inPlaceEditDescription').set(new RichTextInlineEditWidget('event.main.changeDescription', <%= jsonEncode({'conference': "%s"%conferenceId}) %>, confFossile.description).draw());

<% if evtType == 'conference':%>
    <%= macros.genericField(macros.FIELD_RICHTEXT, 'inPlaceEditAdditionalInfo', 'event.main.changeAdditionalInfo', {'conference': "%s"%conferenceId}, preCache=True, rh=self._rh, options=(400,200)) %>
<% end %>

// Room parameters widget
var context = new WidgetEditableContext();

$E('inPlaceEditLocation').set([
  WidgetEditable(
    IndicoUI.Widgets.roomParamsShow,
    function(target, source){
        var info = $O(source.get().getAll());
        var rbWidget = new RoomBookingWidget(Indico.Data.Locations, info, null, nullRoomInfo(info), <%= favoriteRooms %>, null);
	target.set(rbWidget.draw())
        return {
	  activate: function(){},
	  save: function(){
	    // force the observers to be called,
	    // since objects look immutable to presentation,
	    // as references are compared
	    source.set($O(info.getAll()));
	  },
	  stop: function(){
	    bind.detach(target);
	  }
	};
    }
  )(IndicoUtil.cachedRpcValue(Indico.Urls.JsonRpcService, 'event.main.changeBooking',{conference: '<%= conferenceId %>'}, $O(<%= offlineRequest(self._rh,'event.main.changeBooking',{'conference': "%s"%conferenceId})%>)), context),
    IndicoUI.Aux.defaultEditMenu(context)]);


</script>