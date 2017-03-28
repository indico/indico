<%
    from indico.web.flask.templating import get_template_module
    tpl = get_template_module('events/management/_create_event_button.html')
%>

${ template_hook('global-announcement') }

<div class="page-header clearfix">
        <%include file="SessionBar.tpl" args="dark=False"/>

        ${ template_hook('page-header', category=currentCategory) }

        <!--
            set fixed height on anchor to assure that the height is
            corrected if the image cannot be retrieved (i.e. https problems) -->
        <a style="min-height: 60px;" href="${ url_for_index() }">
            <img class="header-logo" src="${ Config.getInstance().getLogoURL() or systemIcon('logo_indico_bw.png') }">
        </a>

    <div class="global-menu toolbar">
        <a href="${ url_for_index() }">${ _("Home") }</a>
        <a class="arrow js-dropdown" href="#" data-toggle="dropdown">${ _("Create event") }</a>
        <ul class="dropdown">
            <li>
                ${ tpl.create_event_link(currentCategory, 'lecture', _('Create lecture'), id='create-lecture') }
            </li>
            <li>
                ${ tpl.create_event_link(currentCategory, 'meeting', _('Create meeting'), id='create-meeting') }
            </li>
            <li>
                ${ tpl.create_event_link(currentCategory, 'conference', _('Create conference'), id='create-conference') }
            </li>
        </ul>

        % if roomBooking:
            <a href="${ url_for('rooms.roomBooking') }">${ _("Room booking") }</a>
        % endif

        % if len(adminItemList) == 1:
            <a href="${ adminItemList[0]['url'] }">${ adminItemList[0]['text'] }</a>
        % elif len(adminItemList) > 1:
            <a class="arrow js-dropdown" href="#" data-toggle="dropdown">${ _("Administration") }</a>
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
                <a class="arrow js-dropdown" href="#" data-toggle="dropdown">${ dropdown_title }</a>
                <ul class="dropdown">
                    % for item in items:
                        <li><a href="${ item.url }">${ item.caption }</a></li>
                    % endfor
                </ul>
            % endif
        % endfor

        % if _session.user:
            <a href="${ url_for('users.user_dashboard', user_id=None) }">${ _("My profile") }</a>
        % endif

        <a class="arrow js-dropdown" href="#" data-toggle="dropdown">${ _("Help") }</a>
        <ul class="dropdown">
            <li>
                <a style="color: #777; cursor: initial;"
                   title="We are working on updating the documentation. Stay tuned!">
                    ${ _("Indico help") }
                </a>
            </li>
            % if show_contact:
                <li><a href="${ url_for('misc.contact') }">${ _("Contact") }</a></li>
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
  });
</script>
