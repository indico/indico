<%page args="evtType=None, confObj=None"/>
<%

# maybe all of this should be moved to the W* class?

from MaKaC.fossils.conference import IConferenceFossil
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


favoriteRooms = confObj.getFavoriteRooms()

additionalInfo = confObj.getContactInfo()

%>
<div class="groupTitle">${ _("General Settings")}</div>

<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat">${ _("Title")}</span>
    </td>
    <td class="blacktext" style="width:100%">
        <span id="inPlaceEditTitle">${title }</span>
    </td>
</tr>
<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat">${ _("Description")}</span>
    </td>
    <td>
        <div class="blacktext" id="inPlaceEditDescription">${description }</div>
    </td>
</tr>
<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat">${ _("Place")}</span>
    </td>
    <td class="blacktext" id="inPlaceEditLocation">
        <strong>${ _("Location:")} </strong>
        <span id="inPlaceEditLocationName">${locationName }</span>
        <br/>
        <strong>${ _("Address:")} </strong>
        <span id="inPlaceEditLocationAddress">${locationAddress }</span>
        <br/>
        <strong>${ _("Room:")} </strong>
        <span id="inPlaceEditLocationRoom">${locationRoom }</span>
        <div id="inPlaceEditLocation_Menu">
        </div>
    </td>
</tr>
<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat">${ _("Start/End date")}</span>
    </td>
    <td class="blacktext">
        <span id="inPlaceEditStartEndDate">${startDate } <strong>to</strong> ${ endDate }</span>
    </td>
</tr>
<!-- Fermi timezone awareness -->
<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat">${ _("Timezone")}</span>
    </td>
     <td class="blacktext">
        <span id="inPlaceEditTimezone">${timezone}</span>
    </td>
</tr>
<!-- Fermi timezone awareness(end) -->
% if evtType == 'conference':
<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat">${ _("Additional info")}</span>
    </td>
    <td class="blacktext">
        <span id="inPlaceEditAdditionalInfo">${contactInfo}</span>
    </td>
</tr>
% endif
<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat">${ _("Support") }</span>
    </td>
    <td class="blacktext">
        <span id="inPlaceEditSupport">${ supportEmail }</span>
    </td>
</tr>
% if evtType == 'lecture':
<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat">${ _("Organisers")}</span>
    </td>
    <td class="blacktext">
        <span id="inPlaceEditOrganiserText">${confObj.getOrgText() }</span>
    </td>
</tr>
% endif
<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat">${ _("Default style")}</span>
    </td>
    <td class="blacktext">
        <span id="inPlaceEditDefaultStyle">${defaultStyle }</span>
    </td>
</tr>
<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat">${ _("Visibility")}</span>
    </td>
    <td class="blacktext">
        <span id="inPlaceEditVisibility">${visibility }</span>
    </td>
</tr>
<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat">${ _("Event type")}</span>
    </td>
    <td class="blacktext">
        <span id="inPlaceEditType">${eventType }</span>
    </td>
</tr>
<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat">${ _("Keywords")}</span>
    </td>
    <td class="blacktext">
        <span id="inPlaceEditKeywords">${keywords }</span>
    </td>
</tr>

<tr>
    % if Config.getInstance().getShortEventURL() != "":
      <td class="dataCaptionTD">
        <span class="dataCaptionFormat">${ _("Short display URL")}</span>
      </td>
      <td  class="blacktext">
          <span id="inPlaceEditShortURL">${shortURLTag}</span>
      </td>
    % endif
</tr>

<tr>
    <td></td>
    <td style="vertical-align: bottom;text-align:right">
        <form action=${ dataModificationURL } method="post">
            <input type="submit" class="btn" value="${_('Edit all')}"/>
        </form>
    </td>
</tr>

<tr>
    <td colspan="3" class="horizontalLine">
        &nbsp;
    </td>
</tr>
<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat">${ _("Speakers") if evtType == 'lecture' else  _("Chairpersons")}</span>
    </td>
    <td colspan="2">
        <table width="100%">
            <tr>
                <td class="blacktext" style="width: 79%">
                    <ul id="chairPersonsList" class="UIAuthorList"></ul>
                </td>
                <td nowrap valign="top" style="width: 21%; text-align:right; padding-top:5px; padding-bottom:5px;">
                    <span id="addNewChairSpan" onmouseover="this.className = 'mouseover'" onmouseout="this.className = ''">
                        <a id="addNewChairLink" class="dropDownMenu fakeLink">${ _("Add chairperson") if eventType == "conference" or eventType == "meeting" else  _("Add speaker")}</a>
                    </span>
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

var confFossile = ${ jsonEncode(confObj.fossilize(IConferenceFossil, tz=confObj.getTimezone())) };

$E('inPlaceEditTitle').set(new InputEditWidget('event.main.changeTitle',
        {'conference':'${ conferenceId }'}, ${ jsonEncode(title) }, false, null, null,
        null).draw());

$E('inPlaceEditSupport').set(new SupportEditWidget('event.main.changeSupport', ${ jsonEncode(dict(conference="%s"%conferenceId)) }, {'caption': confFossile.supportInfo.caption, 'email': confFossile.supportInfo.email, 'telephone': confFossile.supportInfo.telephone}).draw());

% if evtType == 'lecture':
    $E('inPlaceEditOrganiserText').set(new InputEditWidget('event.main.changeOrganiserText',
            {'conference':'${ conferenceId }'}, ${ jsonEncode(confObj.getOrgText()) }, true, null, null,
            null).draw());
% endif

<%
from MaKaC.common import info
styleOptions = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager().getStyleDictForEventType(confObj.getType())
styleOptions = dict(map(lambda k: (k, styleOptions[k][0]), styleOptions))
%>

$E('inPlaceEditDefaultStyle').set(new SelectEditWidget('event.main.changeDefaultStyle',
        {'conference':'${ conferenceId }'}, ${ styleOptions }, ${ jsonEncode(defaultStyle) }, null).draw());

$E('inPlaceEditVisibility').set(new SelectEditWidget('event.main.changeVisibility',
        {'conference':'${ conferenceId }'}, ${ visibilityList }, ${ jsonEncode(visibility) }, null).draw());

$E('inPlaceEditType').set(new SelectEditWidget('event.main.changeType',
        {'conference':'${ conferenceId }'}, ${ typeList }, ${ jsonEncode(eventType) }, null).draw());

$E('inPlaceEditStartEndDate').set(new StartEndDateWidget('event.main.changeDates', ${ jsonEncode(dict(conference="%s"%conferenceId)) }, {'startDate': confFossile.startDate, 'endDate': confFossile.endDate}, confFossile.type != 'simple_event').draw());

$E('inPlaceEditDescription').set(new ParsedRichTextInlineEditWidget('event.main.changeDescription', ${ jsonEncode(dict(conference="%s"%conferenceId)) }, confFossile.description, null, null, "${_('No description')}").draw());

var userCaption = "speaker";

% if evtType == 'conference':
    $E('inPlaceEditAdditionalInfo').set(new RichTextInlineEditWidget('event.main.changeAdditionalInfo', ${ jsonEncode(dict(conference="%s"%conferenceId)) }, ${ jsonEncode(additionalInfo) }, 600, 45, "${_('No additional info')}").draw());
    userCaption = "chairperson";
% endif

$E('inPlaceEditShortURL').set(new URLPathEditWidget('event.main.changeShortURL',
        {'conference':'${ conferenceId }'}, ${ jsonEncode(shortURLBase) }, ${ jsonEncode(shortURLTag) }, true, null, function(value) {
            return IndicoUtil.parseShortURL(value);
        }, $T("The short URL contains invalid characters. The allowed characters are alphanumeric, /, _, - and .")).draw());

$E('inPlaceEditKeywords').set(new TextAreaEditWidget('event.main.changeKeywords', ${ jsonEncode(dict(conference="%s"%conferenceId)) }, ${ jsonEncode(keywords) }).draw());

var timezoneList = $D(${dict((item,item) for item in timezoneList)| n,j});

timezoneList.sort(function(val1, val2){
return SortCriteria.Default(timezoneList.get(val1), timezoneList.get(val2));
});


$E('inPlaceEditTimezone').set(new SelectEditWidget('event.main.changeTimezone',
        {'conference':'${ conferenceId }'}, timezoneList, ${ jsonEncode(timezone) }, null).draw());


// Room parameters widget
var context = new WidgetEditableContext();

$E('inPlaceEditLocation').set([
  WidgetEditable(
    IndicoUI.Widgets.roomParamsShow,
    function(target, source){
        var info = $O(source.get().getAll());
        var rbWidget = new RoomBookingWidget(Indico.Data.Locations, info, null, nullRoomInfo(info), ${ favoriteRooms }, null);
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
  )(IndicoUtil.cachedRpcValue(Indico.Urls.JsonRpcService, 'event.main.changeBooking',{conference: '${ conferenceId }'}, $O(${currentLocation | n,j})), context),
    IndicoUI.Aux.defaultEditMenu(context)]);

// Search chairpersons/speakers

var chairPersonsManager = new ParticipantsListManager(confFossile["id"],
        {'addNew': 'event.main.addNewChairPerson',
         'addExisting': 'event.main.addExistingChairPerson',
         'remove': 'event.main.removeChairPerson',
         'edit': 'event.main.editChairPerson',
         'sendEmail': 'event.main.sendEmailData',
         'changeSubmission': 'event.main.changeSubmissionRights'},
        {confId: confFossile["id"], kindOfList: "chairperson"}, $E('chairPersonsList'), $E('addNewChairSpan'),
         "chairperson", "chairperson", "conference", "UIAuthorMove",  ${chairpersons | n,j});
</script>
