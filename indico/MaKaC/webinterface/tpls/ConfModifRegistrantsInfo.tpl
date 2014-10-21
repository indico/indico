<%!
    from babel.numbers import format_currency
%>
<%def name="generate_table(table)">
    <table class="registrant-stats">
    % if table.get('head'):
        <thead>
            <tr>
            % for head in table['head']:
                % if head.type == 'str':
                    <th
                    % if head.colspan > 1:
                        colspan="${ head.colspan }"
                    % endif
                    >${ head.data }</th>
                % endif
            % endfor
            </tr>
        </thead>
    % endif
    % if table.get('rows'):
        <tbody>
        % for row_type, row in table['rows']:
            <tr class="${ row_type } ${'cancelled-row' if is_cancelled else ''}"
                % if is_cancelled:
                    title="${_("Cancelled Event") }: ${ cancel_reason }"
                    data-qtip-opts='{"position":{"at": "left center", "my": "right center"}}'
                % endif
            >
            % for cell in row:
                ${ generate_data_cell(cell) }
            % endfor
            </tr>
        % endfor
        </tbody>
    % endif
    </table>
</%def>
<%def name="generate_data_cell(cell)">
        <td
            % if cell.colspan > 1:
                colspan="${ cell.colspan }"
            % endif
            % if cell.qtip:
                title="${ cell.qtip }"
            % endif
            % if cell.classes:
                class="${ ' '.join(cell.classes) }"
            % endif
        >
    % if cell.type == 'progress-stacked':
        <span class="i-progress
        % if len(cell.data[1]) < 10:
            i-progress-small
        % elif len(cell.data[1]) > 14:
            i-progress-large
        % endif
        ">
            % for width in cell.data[0]:
                <span class="i-progress-bar" style=${ '"width:{:%};"'.format(width) }></span>
            % endfor
            <span class="i-progress-label">${ cell.data[1] }</span>
        </span>
    % elif cell.type == 'progress':
        <span class="i-progress
        % if len(cell.data[1]) < 10:
            i-progress-small
        % elif len(cell.data[1]) > 14:
            i-progress-large
        % endif
        ">
            <span class="i-progress-bar" style=${ '"width:{:%};"'.format(cell.data[0]) }></span>
            <span class="i-progress-label">${ cell.data[1] }</span>
        </span>
    % elif cell.type == 'currency':
        <span>${ format_currency(cell.data[0], cell.data[1], locale=_session.lang) }</span>
    % elif cell.type == 'str':
        <span>${ cell.data }</span>
    % elif cell.type == 'icon':
        <span style="display: block; text-align:center;"><i class="icon-${ cell.data }"></i></span>
    % else:
        <span class="no-stats-data" style="display: block; text-align:center;">&mdash;</i></span>
    % endif
</%def>
<span>
    <a class="i-button" href=${ backURL }><i class="icon-prev"></i> ${ _("back to registrants list")}</a>
</span>
<h2 class="group-title">${ _("Registrants Statistics")} &mdash; ${ no_registrants } ${ _("registrants selected") }</h2>
<div class="i-box-group horz vert">
    %if numAccoTypes > 0:
    <div class="i-box titled">
        <div class="i-box-header">
            <div class="i-box-title">${ accoCaption }</div>
        </div>
        <div class="i-box-content">
            <table class="registrant-stats" cellspacing="0">
            ${ accommodationTypes }
            </table>
        </div>
    </div>
    %endif
    % if social_events:
    <div class="i-box titled registrant-stats">
        <div class="i-box-header">
            <div class="i-box-title">${ social_events.title }</div>
            <div class="i-box-text">
            <% mandatory_text = '<b>{}</b>'.format(_("must")) if social_events.mandatory else _("can") %>
            % if social_events.selection_type == 'unique':
                ${ _("Registrants {} select a single event.").format(mandatory_text) }
            % elif social_events.selection_type == 'multiple':
                ${ _("Registrants {} select multiple events.").format(mandatory_text) }
            % endif
            </div>
        </div>
        <div class="i-box-content">
            ${ generate_table(social_events.get_table()) }
        </div>
    </div>
    % endif
    %if numSessions > 0:
    <div class="i-box titled">
        <div class="i-box-header">
            <div class="i-box-title">${ sessionsCaption }</div>
        </div>
        <div class="i-box-content">
            <table class="registrant-stats" cellspacing="0">
            ${ sessions }
            </table>
        </div>
    </div>
    %endif
</div>
<script>
    $(document).on('click', 'table.registrant-stats tr.header-row', function toggleSubRows(evt) {
        $(this).nextUntil('tr.header-row, tr.single-row').toggle();
        $(this).toggleClass('collapsed');
    });
</script>
