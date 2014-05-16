<h2 class="page-title">
    ${ _('Calendar') }
</h2>

% if overload:
    <div class="error-message-box">
        <div class="message-text">
            ${ _('The period may not be longer than {0} days.').format(max_days) }
        </div>
    </div>
% endif

${ calendar }
