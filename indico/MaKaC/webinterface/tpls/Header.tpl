% if self_._rh.isMobile() and Config.getInstance().getMobileURL():
    <%include file="MobileDetection.tpl"/>
% endif

<%include file="Announcement.tpl"/>

<%
urlConference = urlHandlers.UHConferenceCreation.getURL(currentCategory)
urlConference.addParam("event_type","conference")

urlLecture = urlHandlers.UHConferenceCreation.getURL(currentCategory)
urlLecture.addParam("event_type","lecture")

urlMeeting = urlHandlers.UHConferenceCreation.getURL(currentCategory)
urlMeeting.addParam("event_type","meeting")
%>

<div class="page-header clearfix">
        <%include file="SessionBar.tpl" args="dark=False"/>

        ${ template_hook('page-header', category=currentCategory) }

        <!--
            set fixed height on anchor to assure that the height is
            corrected if the image cannot be retrieved (i.e. https problems) -->
        <a style="min-height: 60px;" href="${ url_for_index() }">
            <img class="header-logo" src="${ systemIcon('logo_indico_bw.png') }" />
        </a>

    <div class="global-menu toolbar">
        <a href="${ url_for_index() }">${ _("Home") }</a>
        <a class="arrow" href="#" data-toggle="dropdown">${ _("Create event") }</a>
        <ul class="dropdown">
            <li><a id="create-lecture" href="${ urlLecture }">${ _("Create lecture") }</a></li>
            <li><a id="create-meeting" href="${ urlMeeting }">${ _("Create meeting") }</a></li>
            <li><a id="create-conference" href="${ urlConference }">${ _("Create conference") }</a></li>
        </ul>

        % if roomBooking:
            <a href="${ urlHandlers.UHRoomBookingWelcome.getURL() }">${ _("Room booking") }</a>
        % endif

        % if len(adminItemList) == 1:
            <a href="${ adminItemList[0]['url'] }">${ adminItemList[0]['text'] }</a>
        % elif len(adminItemList) > 1:
            <a class="arrow" href="#" data-toggle="dropdown">${ _("Administration") }</a>
            <ul class="dropdown">
                % for item in adminItemList:
                    <li><a href="${ item['url'] }">${ item['text'] }</a></li>
                % endfor
            </ul>
        % endif

        % for dropdown_title, items in extra_items:
            % if not dropdown_title:
                % for item in items:
                    <a href="${ item.url }">${ item.caption }</a>
                % endfor
            % else:
                <a class="arrow" href="#" data-toggle="dropdown">${ dropdown_title }</a>
                <ul class="dropdown">
                    % for item in items:
                        <li><a href="${ item.url }">${ item.caption }</a></li>
                    % endfor
                </ul>
            % endif
        % endfor

        % if currentUser:
            <a href="${ url_for('users.user_dashboard', user_id=None) }">${ _("My profile") }</a>
        % endif

        <a class="arrow" href="#" data-toggle="dropdown">${ _("Help") }</a>
        <ul class="dropdown">
            <li><a href="${ urlHandlers.UHConferenceHelp.getURL() }">${ _("Indico help") }</a></li>
            % if show_contact:
                <li><a href="${ urlHandlers.UHContact.getURL() }">${ _("Contact") }</a></li>
            % endif
            <li><a href="http://indico-software.org">${ _("More about Indico") }</a></li>
        </ul>
    </div>
</div>

<script type="text/javascript">
  var TIP_TEXT = {
    lecture: ${ _("A <strong>lecture</strong> is a simple event to annouce a talk.<br/><strong>Features</strong>: poster creation, participants management,...") | n,j },
    meeting: ${ _("A <strong>meeting</strong> is an event that defines an agenda with many talks.<br/><strong>Features</strong>: timetable, minutes, poster creation, participants management,...") | n,j},
    conference: ${ _("A <strong>conference</strong> is a complex event with features to manage the whole life cycle of a conference.<br/><strong>Features</strong>: call for abstracts, registration, e-payment, timetable, badges creation, paper reviewing,...") | n,j}
  };

  $(function() {

    ['lecture', 'meeting', 'conference'].forEach(function(evt_type) {
      $('#create-' + evt_type).qtip({
        content: TIP_TEXT[evt_type],
        position: {
          my: 'left center',
          at: 'right center'
        }
      })
    });

    $('.global-menu').dropdown({selector: 'a[data-toggle=dropdown]'});
  })
</script>
