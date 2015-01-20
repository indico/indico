<div class="groupTitle">
    ${_('Edit Abstract - Modification Closed')}
</div>
% if not underReview:
<p>
    ${_('The deadline for abstract modification has now passed, therefore you are no longer able to modify any abstracts for this event.')}
</p>
% else:
<p>
    ${_('This abstract is already under review and therefore you are no longer allowed to modify it.')}
</p>
% endif
<p>
    ${_('If you have further queries, please contact the event organizer.')}
</p>
