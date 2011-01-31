<%!
if bgColorCode:
    bgColorStyle = """ style="background: %s; border-color: %s;" """%(bgColorCode, bgColorCode)
else:
    bgColorStyle = ""

if textColorCode:
    textColorStyle = """ style="color: %s;" """%(textColorCode)
else:
    textColorStyle = ""
%>


<div class="conf clearfix">
    <div class="confheader clearfix" <%= bgColorStyle %>>
        <div class="confTitleBox" <%= bgColorStyle %>>
            <div class="confTitle">
                <h1>
                    <a href="<%= displayURL %>">
                        <span class="conferencetitlelink" style="color:<%= textColorCode %>">
                            <% if logo :%>
                                <div class="confLogoBox">
                                   <%= logo %>
                                </div>
                            <%end%>
                            <%= confTitle %>
                        </span>
                    </a>
                </h1>
           </div>
        </div>
        <div class="confSubTitleBox" <%= bgColorStyle %>>
            <div class="confSubTitleContent">
                <%= searchBox %>
                <div class="confSubTitle" <%= textColorStyle %>>
                   <div class="datePlace">
                        <div class="date"><%= confDateInterval %></div>
                        <div class="place"><%= confLocation %></div>
                        <div class="timezone"><%= timezone %> timezone</div>
                    </div>
                    <% if nowHappening: %>
                        <div class="nowHappening" <%= textColorStyle %>><%= nowHappening %></div>
                    <% end %>
                    <% if onAirURL: %>
                        <div class="webcast" <%= textColorStyle %>>
                            <%= _("Live webcast") %>: <a href="<%= webcastURL  %>"><%= _("view the live webcast") %></a>
                        </div>
                    <% end %>
                    <% if forthcomingWebcast: %>
                        <div class="webcast" <%= textColorStyle %>>
                            <%= _("Webcast") %>:<%= _(" Please note that this event will be available live via the") %>
                            <a href="<%= webcastURL %>"><%= _("Webcast Service") %></a>.
                        </div>
                    <% end %>
                </div>
            </div>
        </div>
        <% if simpleTextAnnouncement: %>
            <div class="simpleTextAnnouncement"><%= simpleTextAnnouncement %></div>
        <% end %>
    </div>
    <div id="confSectionsBox" class="clearfix">
    <%= menu %>
    <%= body %>
    </div>
</div>