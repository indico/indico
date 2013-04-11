
<% import MaKaC.webinterface.urlHandlers as urlHandlers %>

<div class="groupTitle" id="userSection">${ _("Favorite users and categories")}</div>
<div id="userBasketContainer" style="padding: 10px; float: left;">
<!-- Filled through DOM manipulation   -->
</div>
<div id="favoriteBasketContainer" style="padding: 10px; float: left;">
    <div class="FavoritePeopleListDiv">
        <ul class="PeopleList">
            % for entry in favoriteCategs:
                <li data-categ-id="${entry['id']}" class="favoriteCateg">
                    <span class="toggle" style="float: right; clear: both; padding-right: 10px;">
                        <img src="images/remove.png" alt="del" style="vertical-align: middle;" />
                    </span>
                    <span>${entry['title']}</span>
                </li>
            % endfor
        </ul>
    </div>
</div>

<script type="text/javascript">

    var favouriteUserList = ${ offlineRequest(self_._rh, 'user.favorites.listUsers',dict(userId=user.getId())) };

    var removeUser = function(user, setResult){
        jsonRpc(Indico.Urls.JsonRpcService, "user.favorites.removeUser",
                { userId: '${user.getId()}',
                  value: [{'id': user.get('id')}]},
                function(result, error){
                    if (exists(error)) {
                        IndicoUtil.errorReport(error);
                        setResult(false);
                    } else {
                        setResult(true);
                    }
                });
    };

    var addUsers = function(list, setResult){
        jsonRpc(Indico.Urls.JsonRpcService, "user.favorites.addUsers",
                { userId: '${user.getId()}',
                  value: list },
                function(result, error){
                    if (exists(error)) {
                        IndicoUtil.errorReport(error);
                        setResult(false);
                    } else {
                        setResult(true);
                    }
                });
    };


    var uf = new UserListField(
            'FavoritePeopleListDiv', 'PeopleList',
            favouriteUserList, false, null,
            true, false, null, null,
            false, false, false, false,
            addUsers, null, removeUser);

    $E('userBasketContainer').set(uf.draw());

    $('.favoriteCateg').each(function () {
        var $this = $(this);
        $('.toggle', this).css('cursor', 'pointer').on('click', function() {
            indicoRequest('category.favorites.delCategory', {
                categId: $this.data('categId').toString()
            }, function(result, error) {
                if(error) {
                    IndicoUtil.errorReport(error);
                    return;
                }
                $this.remove();
            });
        });
    });
</script>
