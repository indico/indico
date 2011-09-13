${ existingMaterialsTitle }

<div id="materialListPlace"><!-- DOM-filled materials list --></div>
<span id="container"></span>

<script type="text/javascript">

function contains(a, obj){
    for(var i = 0; i < a.length; i++) {
      if(a[i] === obj){
        return true;
      }
    }
    return false;
}

var showMainResourceOption = false;
var mode = '${ mode }';

<% import MaKaC.conference as conference %>
<% from MaKaC.common.fossilize import fossilize %>
<% from MaKaC.conference import IMaterialFossil %>


% if isinstance(self_._target, conference.SubContribution):


    var args = {
        conference: '${ self_._target.getConference().getId() }',
        confId: '${ self_._target.getConference().getId() }',
        contribution: '${ self_._target.getContribution().getId() }',
        contribId: '${ self_._target.getContribution().getId() }',
        subContribution: '${ self_._target.getId() }',
        subContId: '${ self_._target.getId() }',
        parentProtected: ${ jsBoolean(self_._target.isProtected()) }
    };
    var uploadAction = Indico.Urls.UploadAction.subcontribution;
    var targetType = '${ self_._target.getConference().getType() }';
% elif isinstance(self_._target, conference.Contribution):
    var args = {
        conference: '${ self_._target.getConference().getId() }',
        confId: '${ self_._target.getConference().getId() }',
        contribution: '${ self_._target.getId() }',
        contribId: '${ self_._target.getId() }',
        parentProtected: ${ jsBoolean(self_._target.getAccessController().isProtected()) }
    };
    var uploadAction = Indico.Urls.UploadAction.contribution;
    var targetType = '${ self_._target.getConference().getType() }';
    if (targetType == "conference" && mode == 'management') {
        showMainResourceOption = true;
    }
% elif isinstance(self_._target, conference.Session):
    var args = {
        conference: '${ self_._target.getConference().getId() }',
        confId: '${ self_._target.getConference().getId() }',
        session: '${ self_._target.getId() }',
        sessionId: '${ self_._target.getId() }',
        parentProtected: ${ jsBoolean(self_._target.getAccessController().isProtected()) }
    };
    var uploadAction = Indico.Urls.UploadAction.session;
    var targetType = '${ self_._target.getConference().getType() }';
% elif isinstance(self_._target, conference.Conference):
    var args = {
        conference: '${ self_._target.getId() }',
        confId: '${ self_._target.getId() }',
        parentProtected: ${ jsBoolean(self_._target.getAccessController().isProtected()) }
    };
    var uploadAction = Indico.Urls.UploadAction.conference;
    var targetType = '${ self_._target.getConference().getType() }';
% elif isinstance(self_._target, conference.Category):
    var args = {
        category: '${ self_._target.getId() }',
        categId: '${ self_._target.getId() }',
        parentProtected: ${ jsBoolean(self_._target.getAccessController().isProtected()) }
    };
    var uploadAction = Indico.Urls.UploadAction.category;
    var targetType = 'category';
% endif

var matList = ${ fossilize(materialList, IMaterialFossil) };

var mlist = new MaterialListWidget(args, matList, uploadAction, null, null, showMainResourceOption);


$E('materialListPlace').set(mlist.draw());


</script>
