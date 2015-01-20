<div class="title">${ _("Video Services Guides")}</div>
    <div class="content">

    % if IsAdmin:
    <div class="item clearfix">
        <div class="icons">
            <a href="ihelp/html/VideoServicesGuides/AdminGuide/index.html" style="vertical-align: top">
                    Web
            </a> |
            <a href="ihelp/pdf/IndicoVSAdminGuide.pdf">
                <img src="images/pdf_small.png" alt="PDF version">
            </a>
        </div>
        <a href="ihelp/html/VideoServicesGuides/AdminGuide/index.html">${ _("Administrator Guide")}</a>

    </div>
    % endif

    % if IsCollaborationAdmin:
    <div class="item clearfix">
        <div class="icons">
            <a href="ihelp/html/VideoServicesGuides/ManagerOverview/index.html" style="vertical-align: top">
                    Web
            </a> |
            <a href="ihelp/pdf/IndicoVSManagerOverview.pdf">
                <img src="images/pdf_small.png" alt="PDF version">
            </a>
        </div>
        <a href="ihelp/html/VideoServicesGuides/ManagerOverview/index.html">${ _("Manager Overview")}</a>

    </div>
    % endif

    <div class="item clearfix">
        <div class="icons">
            <a href="ihelp/html/VideoServicesGuides/EventManager/index.html" style="vertical-align: top">
                    Web
            </a> |
            <a href="ihelp/pdf/IndicoVSEventManager.pdf">
                <img src="images/pdf_small.png" alt="PDF version">
            </a>
        </div>
        <a href="ihelp/html/VideoServicesGuides/EventManager/index.html">${ _("How to manage video services")}</a>
    </div>

    <div class="item clearfix">
        <div class="icons">
            <a href="ihelp/html/VideoServicesGuides/UserGuide/index.html" style="vertical-align: top">
                    Web
            </a> |
            <a href="ihelp/pdf/IndicoVSUserGuide.pdf">
                <img src="images/pdf_small.png" alt="PDF version">
            </a>
        </div>
        <a href="ihelp/html/VideoServicesGuides/UserGuide/index.html">${ _("How to join a video service")}</a>
    </div>
</div>
