
<% import MaKaC.webinterface.urlHandlers as urlHandlers %>

<table style="border-spacing:50px 5px;">
    <thead>
        <tr>
            <td class="groupTitle">${ _("Favorite Users")}</td>
            <td class="groupTitle">${ _("Favorite Categories")}</td>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>
                <div id="userBasketContainer">
                <!-- Filled through DOM manipulation   -->
                </div>
            </td>
            <td style="vertical-align: top">
                <div id="favoriteBasketContainer">
                    <div class="FavoritePeopleListDiv">
                        <ul class="PeopleList">
                            % for entry in favoriteCategs:
                                <li data-categ-id="${entry['id']}" class="favoriteCateg">
                                    <span class="toggle" style="float: right; clear: both; padding-right: 10px;">
                                        <img src="${Config.getInstance().getBaseURL()}/images/remove.png" alt="del" style="vertical-align: middle;" />
                                    </span>
                                    <span>${entry['title']}</span>
                                </li>
                            % endfor
                        </ul>
                    </div>
                </div>
            </td>
        </tr>
    </tbody>
</table>

<script type="text/javascript">
    var favouriteUserList = ${favoriteUsers | n,j};

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
                userId: '${user.getId()}',
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
