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
