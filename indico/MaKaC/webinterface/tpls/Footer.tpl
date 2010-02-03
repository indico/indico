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

<div id="poweredBy" class="<%if shortURL != "" and not isFrontPage: %>longFooter <% end %>footer<% if dark == True: %> footerDark<% end %>">

<div style="margin-bottom: 15px; font-family: monospace; font-size: 10px;">
  <% if shortURL != "" and not isFrontPage: %>
  <div><%= shortURL %></div>
  <% end %>

  <% if modificationDate != "": %>
  <div><%= _("Last modified: ") + modificationDate %></div>
  <% end %>
</div>


            <img src="<%= systemIcon("indico_small") %>" alt="<%= _("Indico - Integrated Digital Conference")%>" style="vertical-align: middle; margin-right: 2px;"/>
            <span style="vertical-align: middle;"><%= _("Powered by ")%> <a href="http://cdsware.cern.ch/indico/">CDS Indico</a></span>

            <% if Configuration.Config.getInstance().getWorkerName()!="": %>
                <span style="display: none;"><%= Configuration.Config.getInstance().getWorkerName() %></span>
            <% end %>

</div>
