<%page args="parentName=None, privacy=None, parentPrivacy=None, statusColor=None, parentStatusColor=None, locator=None"/>
<%
termsDict={ 'Category': {'name':'category', 'paramsKey': 'categId', 'parentName':'category'},
            'Event':    {'name':'event', 'paramsKey': 'confId', 'parentName':'category'},
            'Session':  {'name':'session', 'paramsKey': 'sessionId', 'parentName':'event'},
            'Contribution': {'name':'contribution', 'paramsKey': 'contribId', 'parentName':'event'},
            'InSessionContribution': {'name':'contribution', 'paramsKey': 'contribId', 'parentName':'session'},
            'SubContribution': {'name':'contribution', 'paramsKey': 'contribId', 'parentName':'contribution'}
          }
%>
<tr>
    <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Current status")}</span></td>
    <td bgcolor="white" width="100%" valign="top" class="blacktext">
        <div class="ACStatusDiv">
            ${ _("Your " + termsDict[type]['name'] + " is currently") } <span class="ACStatus" id="privacy_status" style="color: ${statusColor};">${ _(privacy) }</span>
            % if privacy == 'INHERITING' :
                ${ _("from a")} <span style="color: ${parentStatusColor};">${ _(parentPrivacy)}</span> ${ _(termsDict[type]['parentName'])}
            % endif
            </div>
        <div class="ACStatusDescDiv">
            % if privacy == 'PUBLIC' :
                ${ _("This means that it can be viewed by all the users, regardless of the access protection of its parent " + termsDict[type]['parentName']) } '${ parentName }'.
            % elif privacy == 'PRIVATE' :
                ${ _("This means that it can be viewed only by the users you specify in the following list, regardless of the access protection of the parent  " + termsDict[type]['parentName']) } '${ parentName }'.
            % elif privacy == 'INHERITING' :
                ${ _("This means that it has the same access protection as its parent " + termsDict[type]['parentName']) } '${ parentName }' ${ _("which is currently ")}
                <span class='ACStatus' style="color: ${parentStatusColor};">${ _(parentPrivacy)}</span> ${ _("(but this may change).")}
                % if parentPrivacy == 'PRIVATE' :
                <br/>
                ${ _("You can specify users allowed to access your " + termsDict[type]['name'])} <strong>${ _("in addition")}</strong>
                ${ _(" to the ones already allowed to access the parent " + termsDict[type]['parentName'])} '${ parentName }'
                ${ _("by adding them to the list below. This won't change the access protection of the parent " + termsDict[type]['parentName'] + ".")}
                % endif
            % endif
        </div>

        % if not target.getAccessController().isFullyPublic() and (privacy == 'PUBLIC' or (privacy == 'INHERITING' and parentPrivacy == 'PUBLIC')):
                <div class="noninherited_children_danger">
                  <i class="icon-shield"></i>
                  <span>
                    ${_('Some parts of it are accesible only for authorized people. <a href="#" class="see_children" data-url="{0}.protection.getChildrenProtected" data-type="Protected">Which ones?</a>').format(termsDict[type]['name'])}
                  </span>
                </div>
        % elif not target.getAccessController().isFullyPrivate() and (privacy == 'PRIVATE' or (privacy == 'INHERITING' and parentPrivacy == 'PRIVATE')):
                <div class="noninherited_children_danger">
                  <i class="icon-shield"></i>
                  <span>
                    ${_('Some parts of it are accesible for everybody. <a href="#" class="see_children" data-url="{0}.protection.getChildrenPublic" data-type="Public">Which ones?</a>').format(termsDict[type]['name'])}
                  </span>
                </div>
                % if len(target.getAccessController().getChildrenProtected()) > 0:
                <div class="noninherited_children_warning">
                  <i class="icon-shield"></i>
                  <span>
                    ${_('Some other parts are still protected but their protection has been redefined. <a href="#" class="see_children" data-url="{0}.protection.getChildrenProtected" data-type="Protected">Which ones?</a>').format(termsDict[type]['name'])}
                  </span>
                </div>
                %endif
        % endif

       % if privacy == 'PRIVATE' or (privacy == 'INHERITING' and parentPrivacy == 'PRIVATE') :
       <div class="ACUserListDiv">
           <div class="ACUserListWrapper" id="ACUserListWrapper">
           </div>
       </div>
       % endif
    </td>
</tr>
% if privacy == 'PRIVATE' or (privacy == 'INHERITING' and parentPrivacy == 'PRIVATE') :
<tr>
    <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Contact in case of no access")}</span></td>
    <td bgcolor="white" width="100%" valign="top" class="blacktext">
    <span id="inPlaceEditContact"></span></td>
</tr>
% endif
<tr>
    <td nowrap class="titleCellTD"><span class="titleCellFormat"> ${ _("Modify status")}</span></td>
    <td bgcolor="white" width="100%" valign="top" class="blacktext">
    <div class="ACModifDiv">
        <form action="${ setPrivacyURL }" method="POST">
            ${ locator }
            <div class="ACModifButtonsDiv">
                % if privacy == 'PRIVATE' or privacy == 'INHERITING':
                <div class="ACModifButtonEntry">
                    ${ _("Make it")} <input type="submit" class="btn" name="changeToPublic" value="${ _("PUBLIC")}"> ${ _("(viewable by all the users, regardless of the access protection of the parent " + termsDict[type]['parentName'])} '${ parentName }').
                </div>
                % endif
                % if privacy == 'PUBLIC' or privacy == 'INHERITING':
                <div class="ACModifButtonEntry">
                    ${ _("Make it")} <input type="submit" class="btn" name="changeToPrivate" value="${ _("PRIVATE")}"> ${ _("(viewable only by the users you choose, regardless of the access protection of the parent " + termsDict[type]['parentName'])} '${ parentName }').
                </div>
                % endif
                % if privacy == 'PUBLIC' or privacy == 'PRIVATE':
                <div class="ACModifButtonEntry">
                    ${ _("Make it")} <input type="submit" class="btn" name="changeToInheriting" value="${ _("INHERITING")}"> ${ _("the access protection from its parent " + termsDict[type]['parentName'])} '${ parentName }' (<span class=ACStatus style="color: ${parentStatusColor};">${ _(parentPrivacy)}</span> ${ _("for the moment).")}
                </div>
                % endif
            </div>
            <input type="hidden" name="type" value=${ type }>
        </form>
    </div>
    </td>
</tr>
<script type="text/javascript">

% if not target.getAccessController().isFullyPublic() and (privacy == 'PUBLIC' or (privacy == 'INHERITING' and parentPrivacy == 'PUBLIC')) \
    or not target.getAccessController().isFullyPrivate() and (privacy == 'PRIVATE' or (privacy == 'INHERITING' and parentPrivacy == 'PRIVATE')):
    $(".see_children").click(function(){
        var self = this;
        var killProgress = IndicoUI.Dialogs.Util.progress($T("Getting children protected elements..."));
        jsonRpc(Indico.Urls.JsonRpcService, $(self).data("url") ,
                {${ termsDict[type]['paramsKey'] }: '${ target.getId() }',
                % if type != 'Event':
                    'confId' : '${ target.getConference().getId() }',
                % endif
                },
                function(result, error){
                    if (exists(error)) {
                        killProgress();
                        IndicoUtil.errorReport(error);
                    } else {
                        killProgress();
                        new ChildrenProtectionPopup($(self).data("type") + $T(" children list"), result).open();
                    }
                });
        });
% endif

% if privacy == 'PRIVATE' or (privacy == 'INHERITING' and parentPrivacy == 'PRIVATE') :
    new IndicoUI.Widgets.Generic.textField($E('inPlaceEditContact'), '${termsDict[type]['name'] + '.protection.changeContactInfo'}', ${dict([(termsDict[type]['paramsKey'], target.getId())])}, '${contactInfo or _("no contact info defined")}');
    % if type != 'Category' and type!= 'Home' and type != 'Event':
    var allowedList = ${ offlineRequest(self_._rh, termsDict[type]['name'] + '.protection.getAllowedUsersList', dict([(termsDict[type]['paramsKey'], target.getId()), ('confId', target.getConference().getId())])) };
    % else :
    var allowedList = ${ offlineRequest(self_._rh, termsDict[type]['name'] + '.protection.getAllowedUsersList', dict([(termsDict[type]['paramsKey'], target.getId())])) };
    % endif

    var removeUser = function(user, setResult){
        // This operation may be very expensive for categories
        % if type == 'Category' or type == 'Home' :
        var killProgress = IndicoUI.Dialogs.Util.progress($T("This operation may take a few minutes..."));
        % endif
        jsonRpc(Indico.Urls.JsonRpcService, "${ termsDict[type]['name'] }.protection.removeAllowedUser",
                {${ termsDict[type]['paramsKey'] }: '${ target.getId() }',
                % if type != 'Category' and type!= 'Home' and type != 'Event':
                    'confId' : '${ target.getConference().getId() }',
                % endif
                    value: {'id': user.get('id')}},
                function(result, error){
                    if (exists(error)) {
                        % if type == 'Category' or type == 'Home' :
                        killProgress();
                        % endif
                        IndicoUtil.errorReport(error);
                        setResult(false);
                    } else {
                        % if type == 'Category' or type == 'Home' :
                        killProgress();
                        % endif
                        setResult(true);
                    }
                });
    };

    var addUsers = function(list, setResult){
        // This operation may be very expensive for categories
        % if type == 'Category' or type == 'Home' :
        var killProgress = IndicoUI.Dialogs.Util.progress($T("This operation may take a few minutes..."));
        % endif
        jsonRpc(Indico.Urls.JsonRpcService, "${termsDict[type]['name']}.protection.addAllowedUsers",
                {${ termsDict[type]['paramsKey'] }: '${ target.getId() }',
                % if type != 'Category' and type!= 'Home' and type != 'Event':
                    'confId' : '${ target.getConference().getId() }',
                % endif
                    value: list },
                function(result, error){
                    if (exists(error)) {
                        % if type == 'Category' or type == 'Home' :
                        killProgress();
                        % endif
                        IndicoUtil.errorReport(error);
                        setResult(false);
                    } else {
                        % if type == 'Category' or type == 'Home' :
                        killProgress();
                        % endif
                        setResult(true);
                    }
                });
    };

    // ---- List of users allowed to view the categ/event/material/resource

    var allowedUsersList = new UserListField(
            'userListDiv', 'userList',
            allowedList, true, null,
            true, true, null, null,
            false, false, true,
            addUsers, null, removeUser);

    // ---- On Load

    IndicoUI.executeOnLoad(function()
    {
        $E('ACUserListWrapper').set(allowedUsersList.draw());
    });
% endif
</script>
