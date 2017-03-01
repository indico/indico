<h2 class="page-title">
    ${ _('Book a room') }
</h2>

<ul id="breadcrumbs" style="margin: 0px 0px 0px -15px; padding: 0; list-style: none;">
    <!-- the href of the following link is intentionally left empty since we just want to switch to GET -->
    <li><span><a href="">${ _('Specify Search Criteria') }</a></span></li>
    <li><span class="current">${ _('Select Available Period') }</span></li>
    <li><span>${ _('Confirm Reservation') }</span></li>
</ul>


<form id="periodForm" method="POST" action="">
    <input type="hidden" name="step" value="2">
    ${ form.csrf_token() }
    ${ period_form.repeat_frequency(style='display: none;') }
    ${ period_form.repeat_interval(type='hidden') }
    ${ period_form.start_dt(type='hidden') }
    ${ period_form.end_dt(type='hidden') }
    ${ period_form.room_id() }
</form>

<div style="display:none;">
    <div id='booking-dialog'>
        <div id="booking-dialog-content" class="dialog-content"></div>
    </div>
</div>


${ calendar }
