<div class="regFormDialogEditLine">
    <label class="regFormDialogCaptionLine">{% _ 'Cancellation of the "{0}" social event').format('<span id="cancelEventCaption"></span>' %}</label>
</div>
<div class="regFormDialogEditLine">
    <label class="regFormDialogCaption">{% _ 'Reason' %}</label>
     <textarea id="cancelledReason" cols="40" rows="6"></textarea>
</div>
<div class="regFormEditLine" style="margin-bottom: 20px;">
    <button id="cancelEvent">{% _ 'Cancel Event' %}</button>
    <button id="undoCancelEvent">{% _ 'Undo' %}</button>
</div>
