<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.webinterface.rh.conferenceBase import RHSubmitMaterialBase %>
%(existingMaterialsTitle)s
<div id="reviewingMaterialListPlace"><!-- DOM-filled materials list --></div>
<span id="container"></span>

                                   
<script type="text/javascript">

<% import MaKaC.conference as conference %>

var args = {
        conference: '<%= self._target.getConference().getId() %>',
        confId: '<%= self._target.getConference().getId() %>',
        contribution: '<%= self._target.getId() %>',
        contribId: '<%= self._target.getId() %>'
    };
    var uploadAction = Indico.Urls.UploadAction.contribution;
    
var mlist = new ReviewingMaterialListWidget(args, <%= RHSubmitMaterialBase._allowedMatsforReviewing %>, uploadAction);

$E('reviewingMaterialListPlace').set(mlist.draw());

</script>

