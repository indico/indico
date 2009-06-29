<% import MaKaC.common.Configuration as Configuration %>
<%!
try:
    dark
except NameError:
    dark = False;
%>

<!-- TODO: remove? -->
<script type="text/javascript">
function envoi(){
	//alert('Le code de la langue choisie est '+document.forms["changeSesLang"].elements["lang"].value)
	document.forms["changeSesLang"].submit()
}
</script>

<!-- TODO: remove permanently? -->
<% if isFrontPage: %>
	<div id="policyOfUse">
		<h1>Policy of Use</h1>
		If you want to use it for CERN-related projects, please contact <a href="mailto:indico-support@cern.ch"> Indico support</a>.
        Non-CERN institutes may install the Indico software locally under GNU General Public License
        (see the <a href="http://cern.ch/indico">project web site</a>).
	</div>
<% end %>

<div id="poweredBy" class="footer<% if dark == True: %> footerDark<% end %>">
            <a href="http://www.cern.ch">
            <img src="<%= systemIcon("cern_small") %>" alt="Indico - Integrated Digital Conference" />
            </a>
            Powered by CERN
            
            <a href="http://cern.ch/indico">
                Indico
                <% if Configuration.Config.getInstance().getVersion() != "0":%>
                    <%= Configuration.Config.getInstance().getVersion() %>
                <% end %>
            </a>
            
            <% if Configuration.Config.getInstance().getWorkerName()!="": %>
                <span style="display: none;"><%= Configuration.Config.getInstance().getWorkerName() %></span>
            <% end %>
            
            <% if shortURL != "" and not isFrontPage: %>
                <span class="separator">|</span>
                <span><%= shortURL %></span>
            <% end %>
        
            <% if modificationDate != "": %>
                <span class="separator">|</span>
                <span><%= _("Last modified: ") + modificationDate %></span>
            <% end %>
</div>

