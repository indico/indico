
<% import MaKaC.webinterface.urlHandlers as urlHandlers %>

<div class="groupTitle" id="userSection"><%= _("Favorite users")%></div>
<div id="basketContainer" style="padding: 10px;">
<!-- Filled through DOM manipulation   -->
</div>

<script type="text/javascript">	

    var userList = <%= offlineRequest(self._rh, 'user.favorites.listUsers', {}) %>;            
    var removeUser = function(user, setResult){
	
        jsonRpc(Indico.Urls.JsonRpcService, "user.favorites.removeUser",
        {value: [{'id': user.get('id')}]}, function(result, error){
            if (exists(error)) {
                IndicoUtil.errorReport(error);
		setResult(false);
            }
            else {
		setResult(true);
            }
        });
    };

    var addUsers = function(list, setResult){
        jsonRpc(Indico.Urls.JsonRpcService, "user.favorites.addUsers", {
	        value: list
                }, function(result, error){
		    if (exists(error)) {
		        IndicoUtil.errorReport(error);
			setResult(false);
                    }
	            else {
		        setResult(true);
	            }
            });
    };


    var uf = new UserListField('FavoritePeopleListDiv', 'PluginPeopleList',
                    userList,
		    null,
		    null,
		    true, false, false,
		    addUsers, userListNothing, removeUser)
    
    $E('basketContainer').set(uf.draw());

</script>
