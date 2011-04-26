<%
from MaKaC.common.Announcement import getAnnoucementMgrInstance

announcement = getAnnoucementMgrInstance().getText()

%>
% if announcement != '':
    <div class="pageOverHeader clearfix">
        ${ announcement }
    </div>
% endif
