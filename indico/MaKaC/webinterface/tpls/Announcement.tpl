<%
from MaKaC.common.Announcement import getAnnoucementMgrInstance
announcement = getAnnoucementMgrInstance().getText()
%>

% if 'login_as_orig_user' in _session:
    <div class="impersonation-header clearfix">
        <span class="text">
            ${ _('Logged in as') }:
            ${ _session['login_as_orig_user']['user_name'] } &raquo; ${ currentUser.getStraightFullName(upper=False) }
        </span>
        <span class="undo-login-as icon-close contextHelp" title="Switch back to ${ _session['login_as_orig_user']['user_name'] }"></span>
    </div>
% endif

% if announcement != '':
    <div class="pageOverHeader clearfix">
        ${ announcement }
    </div>
% endif
