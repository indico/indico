<% from MaKaC.fossils.user import IAvatarFossil %>

<p style="font-style: italic; padding-bottom: 20px;" >
    Event managers have all the necessary rights for all of the <strong>Video Services</strong> section.<br />
    However, if you want to give other users access to this section, you may do so below.<br />
    They will be able to access the <strong>Video Services</strong> section by clicking in the <strong>Manage event</strong> button in the Event Display page.
</p>

<div style="padding-bottom: 30px;">
    <div class="groupTitle"><%= _("Video Services Managers")%></div>
    <p style="font-style: italic;" >
        Users added here will be able to access <strong>all</strong> of the the Video Services section of this event, including this <strong>Protection</strong> tab.
    </p>
    <div style="padding-left: 20px;"  id="userList_all">
    </div>
</div>

<% allowedPluginNames = [p.getName() for p in CSBM.getAllowedPlugins()] %>
<% allowedPluginNames.sort() %>

<div class="groupTitle"><%= _("Managers for individual systems") %></div>
<p style="font-style: italic;" >
    Users added here will be able to create, edit, delete, etc. bookings / requests for the corresponding plugin only.
</p>

<table>
<% for name in allowedPluginNames: %>
    <tr>
        <td style="vertical-align: top; text-align: right;">
            <span class="dataCaptionFormat"><%= _("Managers for ") + name %></span>
        </td>
        <td style="padding-bottom: 30px;">
            <div style="padding-left: 20px;" id="userList_<%= name %>">
            </div>
        </td>
    </tr>
<% end %>
</table>

<script type="text/javascript">
    <% for name in ["all"] + allowedPluginNames: %>
    var newPersonsHandler = function(userList, setResult) {
        indicoRequest(
            'collaboration.addPluginManager',
            {
                conference: "<%= Conference.getId() %>",
                plugin: "<%= name %>",
                userList: userList
            },
            function(result,error) {
                if (!error) {
                    setResult(true);
                } else {
                    IndicoUtil.errorReport(error);
                    setResult(false);
                }
            }
        );
    }
    var removePersonHandler = function(user, setResult) {
        indicoRequest(
            'collaboration.removePluginManager',
            {
                conference: "<%= Conference.getId() %>",
                plugin: "<%= name %>",
                user: user.get('id')
            },
            function(result,error) {
                if (!error) {
                    setResult(true);
                } else {
                    IndicoUtil.errorReport(error);
                    setResult(false);
                }
            }
        );
    }

    var uf = new NewUserListField('PeopleListDiv', 'PeopleList',
                               <%= jsonEncode(fossilize(CSBM.getPluginManagers(name), IAvatarFossil)) %>,
                               <%= offlineRequest(self._rh, 'user.favorites.listUsers') %>,
                               true, false, false, false,
                               false, false, true,
                               newPersonsHandler, singleUserNothing, removePersonHandler)
    $E('userList_<%=name%>').set(uf.draw())
    <% end %>
</script>
