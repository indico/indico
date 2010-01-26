<div class="container" style="max-width: 700px;">
    <div class="groupTitle"><%= _("Indico help") %></div>
    
    <div class="indicoHelp">
        <div class="title"><%= _("User Guides")%></div>
        
        <div class="content">
            <% if IsAdmin: %>
            <div class="item clearfix">
                <div class="icons"><a href="ihelp/pdf/IndicoAdminGuide.pdf"><img src="images/pdf_small.png" alt="PDF version"></a></div>
                <a href="ihelp/html/AdminGuide/index.html"><%= _("Admin Guide")%></a>
        	</div>
            <% end %>
        
        	<div class="item clearfix">
                <div class="icons"><a href="ihelp/pdf/IndicoUserGuide.pdf"><img src="images/pdf_small.png" alt="PDF version"></a></div>
                <a href="ihelp/html/UserGuide/index.html"><%= _("User Guide")%></a>
        	</div>
        </div>
    
        <% if HasCollaboration: %>
        <div class="title"><%= _("Video Services Guides")%></div>
            <div class="content">
            
            <% if IsAdmin: %>
            <div class="item clearfix">
                <div class="icons">
                    <a href="ihelp/VideoServices/ServerAdminUserGuide_VS/ServerAdminUserGuide_VS.pdf">
                        <img src="images/pdf_small.png" alt="PDF version">
                    </a>
                </div>
                <a href="ihelp/VideoServices/ServerAdminUserGuide_VS/index.html"><%= _("Admin User Guide")%></a>
                <img src="<%= systemIcon('new') %>" style="padding-left: 5px;" alt="new" />
                
            </div>
            <% end %>
            
            <% if IsCollaborationAdmin: %>
            <div class="item clearfix">
                <div class="icons">
                    <a href="ihelp/VideoServices/VSAdminUserGuide_VS/VSAdminUserGuide_VS.pdf">
                        <img src="images/pdf_small.png" alt="PDF version">
                    </a>
                </div>
                <a href="ihelp/VideoServices/VSAdminUserGuide_VS/index.html"><%= _("Video Services Admin User Guide")%></a>
                <img src="<%= systemIcon('new') %>" style="padding-left: 5px;" alt="new" />
                
            </div>
            <% end %>
        
            <div class="item clearfix">
                <div class="icons">
                    <a href="ihelp/VideoServices/EventManagerUserGuide_VS/EventManagerUserGuide_VS.pdf">
                        <img src="images/pdf_small.png" alt="PDF version">
                    </a>
                </div>
                <a href="ihelp/VideoServices/EventManagerUserGuide_VS/index.html"><%= _("Event Manager User Guide")%></a>
                <img src="<%= systemIcon('new') %>" style="padding-left: 5px;" alt="new" />
            </div>
        
            <div class="item clearfix">
                <div class="icons">
                    <a href="ihelp/VideoServices/IndicoUserGuide_VS/IndicoUserGuide_VS.pdf">
                        <img src="images/pdf_small.png" alt="PDF version">
                    </a>
                </div>
                <a href="ihelp/VideoServices/IndicoUserGuide_VS/index.html"><%= _("Indico User Guide")%></a>
                <img src="<%= systemIcon('new') %>" style="padding-left: 5px;" alt="new" />
            </div>
        </div>
        <% end %>
    
    
    	<div class="title"><%= _("Quick Start Guides")%></div>
        <div class="content">
        	<div class="item clearfix">
                <div class="icons"><a href="ihelp/pdf/IndicoQSGContributionManager.pdf"><img src="images/pdf_small.png" alt="PDF version"></a></div>
                <a href="ihelp/html/QuickStartGuides/QSGContributionManager/index.html"><%= _("Contribution Manager")%></a>
        	</div>
        
        	<div class="item clearfix">
                <div class="icons"><a href="ihelp/pdf/IndicoQSGSessionCoordinator.pdf"><img src="images/pdf_small.png" alt="PDF version"></a></div>
                <a href="ihelp/html/QuickStartGuides/QSGSessionCoordinator/index.html"><%= _("Session Coordinator")%></a>
        	</div>
        
        	<div class="item clearfix">
                <div class="icons"><a href="ihelp/pdf/IndicoQSGSessionManager.pdf"><img src="images/pdf_small.png" alt="PDF version"></a></div>
                <a href="ihelp/html/QuickStartGuides/QSGSessionManager/index.html"><%= _("Session Manager") %></a>
        	</div>
        	
        	<div class="item clearfix">
                <div class="icons"><a href="ihelp/pdf/IndicoQSGSubmitter.pdf"><img src="images/pdf_small.png" alt="PDF version"></a></div>
                <a href="ihelp/html/QuickStartGuides/QSGSubmitter/index.html"><%= _("Submitter / Presenter")%></a>
        	</div>
        	
        	<div class="item clearfix">
                <div class="icons"><a href="ihelp/pdf/IndicoQSGTrackCoordinator.pdf"><img src="images/pdf_small.png" alt="PDF version"></a></div>
                <a href="ihelp/html/QuickStartGuides/QSGTrackCoordinator/index.html"><%= _("Track Coordinator") %></a>
        	</div>
            <div class="item clearfix">
                <div class="icons"><a href="ihelp/pdf/IndicoQSGAgendaUsers.pdf"><img src="images/pdf_small.png" alt="PDF version"></a></div>
                <a href="ihelp/html/QuickStartGuides/QSGAgendaUsers/index.html"><%= _("CDS Agenda Users")%></a>
            </div>
        </div>
    
    
    	<div class="title"><%= _("General Help") %></div>
        
        <div class="content">
        	<div class="item clearfix">
                <div class="icons"><a href="ihelp/pdf/IndicoFAQ.pdf"><img src="images/pdf_small.png" alt="PDF version"></a></div>
                <a href="ihelp/html/FAQ/FAQ.html"><%= _("FAQ") %></a>
            </div>
        
            <div class="item clearfix">
                <div class="icons"><a href="ihelp/pdf/IndicoGlossary.pdf"><img src="images/pdf_small.png" alt="PDF version"></a></div>
                <a href="ihelp/html/Glossary/Glossary.html"><%= _("Glossary") %></a>
            </div>
        </div>

    
    	<div class="title"><%= _("Training doc") %></div>
    
        <div class="content">
        	<div class="item clearfix">
                <div class="icons"><a href="ihelp/pdf/handsonmeetings.pdf"><img src="images/pdf_small.png" alt="PDF version"></a></div>
                <%= _("Hands-on - Meetings") %>
        	</div>
        	
            <div class="item clearfix">
                <div class="icons"><a href="ihelp/pdf/handsonconferences.pdf"><img src="images/pdf_small.png" alt="PDF version"></a></div>
                <%= _("Hands-on - Conferences") %>
        	</div>
            
            <div class="item clearfix">
                <div class="icons"><a href="ihelp/pdf/slides.pdf"><img src="images/pdf_small.png" alt="PDF version"></a></div>
                <%= _("Slides") %>
        	</div>
        </div>
    </div>

    <br/>
    <p><em><%= _("You can find more user guides, in different languages, provided by external collaborators") %> <a href="http://cdswaredev.cern.ch/indico/wiki/User/UserGuides">here</a>.</em></p>

</div>