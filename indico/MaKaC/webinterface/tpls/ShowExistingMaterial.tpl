<div class="groupTitle"><%= _("Existing material")%></div>

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

<% import MaKaC.conference as conference %>
<% from MaKaC.common.PickleJar import DictPickler %>


<% if isinstance(self._target, conference.SubContribution): %>


    var args = {
        conference: '<%= self._target.getConference().getId() %>',
        confId: '<%= self._target.getConference().getId() %>',
        contribution: '<%= self._target.getContribution().getId() %>',
        contribId: '<%= self._target.getContribution().getId() %>',
        subContribution: '<%= self._target.getId() %>',
        subContId: '<%= self._target.getId() %>',
        parentProtected: <%= jsBoolean(self._target.isProtected()) %>
    };
    var uploadAction = Indico.Urls.UploadAction.subContribution;
    var targetType = '<%= self._target.getConference().getType() %>';
<% end %>

<% elif isinstance(self._target, conference.Contribution): %>
    var args = {
        conference: '<%= self._target.getConference().getId() %>',
        confId: '<%= self._target.getConference().getId() %>',
        contribution: '<%= self._target.getId() %>',
        contribId: '<%= self._target.getId() %>',
        parentProtected: <%= jsBoolean(self._target.getAccessController().isProtected()) %>
    };
    var uploadAction = Indico.Urls.UploadAction.contribution;
    var targetType = '<%= self._target.getConference().getType() %>';
<% end %>

<% elif isinstance(self._target, conference.Session): %>
    var args = {
        conference: '<%= self._target.getConference().getId() %>',
        confId: '<%= self._target.getConference().getId() %>',
        session: '<%= self._target.getId() %>',
        sessionId: '<%= self._target.getId() %>',
        parentProtected: <%= jsBoolean(self._target.getAccessController().isProtected()) %>
    };
    var uploadAction = Indico.Urls.UploadAction.session;
    var targetType = '<%= self._target.getConference().getType() %>';
<% end %>

<% elif isinstance(self._target, conference.Conference): %>
    var args = {
        conference: '<%= self._target.getId() %>',
        confId: '<%= self._target.getId() %>',
        parentProtected: <%= jsBoolean(self._target.getAccessController().isProtected()) %>
    };
    var uploadAction = Indico.Urls.UploadAction.conference;
    var targetType = '<%= self._target.getConference().getType() %>';
<% end %>

<% elif isinstance(self._target, conference.Category): %>
    var args = {
        category: '<%= self._target.getId() %>',
        categId: '<%= self._target.getId() %>',
        parentProtected: <%= jsBoolean(self._target.getAccessController().isProtected()) %>
    };
    var uploadAction = Indico.Urls.UploadAction.category;
    var targetType = 'category';
<% end %>

var matList = Indico.Data.MaterialTypes[targetType];
var customMatList = $L();

each(<%= jsonEncode(DictPickler.pickle(self._target.getMaterialList())) %>, function(material){
    if (!contains(matList, material.title)){
        customMatList.append(material.title);
    }
    });

var mlist = new MaterialListWidget(args, matList, customMatList, uploadAction);

$E('materialListPlace').set(mlist.draw());

</script>
