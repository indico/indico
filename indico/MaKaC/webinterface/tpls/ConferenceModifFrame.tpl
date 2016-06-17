<%
from MaKaC.webinterface.urlHandlers import UHConferenceModification

event = conf.as_event
cloned_from = event.cloned_from if event.cloned_from_id is not None and not event.cloned_from.is_deleted else None
%>

<div class="layout-side-menu">
    <div class="menu-column">
        <div class="group">
            <a class="icon-switchon highlight i-button"
               title="${ _(u'See the display page of the event')}"
               href="${ url_for('event.conferenceDisplay', event) }">${ _(u'Switch to display view') }</a>
        </div>
    </div>
    <div class="content-column banner">
        <div class="title">
            <a href="${ UHConferenceModification.getURL(conf) }">
                ${ conf.getTitle() | remove_tags } &nbsp;
                <span class="date">
                    % if startDate == endDate:
                        ${ startDate }
                    % else:
                        ${ startDate } - ${ endDate }
                    % endif
                </span>
            </a>
            <div class="subtitle">
                % if cloned_from:
                    ${ _(u'Created by {name} ({email}) from event on <a href="{link}" title="{title}">{date}</a>').format(
                        date=formatDate(cloned_from.start_dt, format="medium"),
                        title=event.title,
                        link=url_for('event_mgmt.conferenceModification', cloned_from),
                        name=event.creator.full_name,
                        email=event.creator.email)}
                % else:
                    ${ _(u"Created by {name} ({email})").format(
                        name=event.creator.full_name,
                        email=event.creator.email)}
                % endif
            </div>
        </div>
        ${ template_hook('event-manage-header', event=conf) }
    </div>
</div>

<div class="layout-side-menu">
    <div id="event-sidemenu" class="menu-column">
        ${ sideMenu }
    </div>
    <div class="content-column">
        ${ render_template('flashed_messages.html') }
        ${ body }
    </div>
</div>
