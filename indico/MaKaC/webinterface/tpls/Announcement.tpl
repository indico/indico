% if 'login_as_orig_user' in _session:
    <div class="impersonation-header clearfix">
        <span class="icon-eye text">
            <small>${ _('Logged in as') }</small>
            <span class="logged-user-name">${ currentUser.getStraightFullName(upper=False) }</span>
            <small>(${ _session['login_as_orig_user']['user_name'] })</small>
        </span>
        <span class="undo-login-as icon-close contextHelp" title="Switch back to ${ _session['login_as_orig_user']['user_name'] }"></span>
    </div>
% endif

% if announcement_header:
    <div class="pageOverHeader clearfix" id="announcementHeader">
        <div class="left clear">
        ${announcement_header}
        </div>
        <div class="icon-close icon-announcement" id="closeAnnouncement"></div>
    </div>
    <script type="text/javascript">
    $('#closeAnnouncement').click(function(){
        $.jStorage.set("hideAnnouncement", "${announcement_header_hash}");
        $('#announcementHeader').slideUp("fast");
    });

    $(function() {
        if($.jStorage.get("hideAnnouncement") != "${announcement_header_hash}"){
            $("#announcementHeader").show();
        }
     });
    </script>
% endif
