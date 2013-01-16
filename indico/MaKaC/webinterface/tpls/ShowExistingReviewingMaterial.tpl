% if ShowWarning:
    <div style="text-align:center;">
        <div class="redWarningMessage" style="display:inline-block"> ${_("""Be aware that the paper has been sent back to the author to make some modifications. If you add
        a new file, the status will change automatically to 'Under Review' and the Author will not be able to submit any file.""")}</div>
    </div>
% endif
<div id="reviewingMaterialListPlace"></div>

<script type="text/javascript">

var args = {
        conference: '${ Contribution.getConference().getId() }',
        confId: '${ Contribution.getConference().getId() }',
        contribution: '${ Contribution.getId() }',
        contribId: '${ Contribution.getId() }',
        parentProtected: ${ jsBoolean(Contribution.getAccessController().isProtected()) }
    };

var mlist = new ReviewingMaterialListWidget(args, [["reviewing", "Reviewing"]], Indico.Urls.UploadAction.contribution, null, null, ${jsonEncode(CanModify)}, $(false), $(false));

$('#reviewingMaterialListPlace').html($(mlist.draw().dom));

</script>
