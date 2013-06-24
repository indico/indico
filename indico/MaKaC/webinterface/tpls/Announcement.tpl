<%
from MaKaC.common.Announcement import getAnnoucementMgrInstance
announcement = getAnnoucementMgrInstance().getText()
%>

% if _session.get('login_as_history'):
    <div class="pageOverHeader impersonation clearfix">
        <em>${ _('Logged in as') }:</em>
        % for entry in _session['login_as_history']:
            ${ entry['user_name'] } &raquo;
        % endfor
        ${ currentUser.getStraightAbrName() }
    </div>
% endif

% if announcement != '':
    <div class="pageOverHeader clearfix">
        ${ announcement }
    </div>
% endif
