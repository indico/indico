<%page args="evtType=None, confObj=None"/>
<%

# maybe all of this should be moved to the W* class?

from MaKaC.fossils.conference import IConferenceFossil
import MaKaC.webinterface.urlHandlers as urlHandlers
from xml.sax.saxutils import escape
from indico.modules.categories.util import get_visibility_options
from indico.modules.events.models.events import EventType

event_types = {t.name: str(t.title) for t in EventType}
visibilityList = dict(get_visibility_options(confObj.as_event))
visibilityList[999] = visibilityList.pop('')

numRows = 11

additionalInfo = confObj.getContactInfo()
%>

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
        ${ render_template('events/management/event_location.html', event=confObj.as_event) }
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
        <span id="inPlaceEditType">${ confObj.as_event.type_.title }</span>
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
    <td colspan="3" class="horizontalLine"></td>
</tr>
<tr>
    <td class="dataCaptionTD">
        <span class="dataCaptionFormat">${ _("Speakers") if evtType == 'lecture' else  _("Chairpersons")}</span>
    </td>
    <td colspan="2">
        ${ render_template('events/management/event_person_links.html', event=confObj.as_event) }
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
    $E('inPlaceEditOrganiserText').set(new TextAreaEditWidget('event.main.changeOrganiserText',
            {'conference':'${ conferenceId }'}, ${ jsonEncode(confObj.getOrgText()) }, true, null, null,
            null).draw());
% endif

$E('inPlaceEditDefaultStyle').set(new SelectEditWidget('event.main.changeDefaultStyle',
        {'conference':'${ conferenceId }'}, ${ styleOptions }, ${ jsonEncode(defaultStyle) }, null).draw());

$E('inPlaceEditVisibility').set(new SelectEditWidget('event.main.changeVisibility',
        {'conference':'${ conferenceId }'}, ${ visibilityList|n,j }, ${ jsonEncode(visibility) }, null).draw());

$E('inPlaceEditType').set(new SelectEditWidget('event.main.changeType',
        {'conference':'${ conferenceId }'}, ${ event_types }, ${ jsonEncode(confObj.as_event.type) }, null).draw());

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
</script>
