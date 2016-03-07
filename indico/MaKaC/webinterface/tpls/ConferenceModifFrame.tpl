<%
from MaKaC.webinterface.urlHandlers import UHConferenceModification

event = conf.as_event
cloned_from = event.cloned_from if event.cloned_from_id is not None and not event.cloned_from.is_deleted else None
%>

<div class="banner">

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

<div class="layout-sidemenu">
    <div id="event-sidemenu" class="sidemenu">${ sideMenu }</div>
    <div class="body">
        ${ render_template('flashed_messages.html') }
        ${ body }
    </div>
</div>
