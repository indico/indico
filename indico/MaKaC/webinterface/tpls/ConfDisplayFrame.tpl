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
    <div class="confheader clearfix" %(bgColorStyle)s>
        <div class="confTitleBox" %(bgColorStyle)s>
            <div class="confTitle">
                <h1>
                    <a href="%(displayURL)s">
                        <span class="conferencetitlelink" style="color:%(textColorCode)s">
                            <% if logo :%>
                                <div class="confLogoBox">
                                   <%= logo %>
                                </div>
                            <%end%>
                            %(confTitle)s
                        </span>
                    </a>
                </h1>
           </div>
        </div>
        <div class="confSubTitleBox" %(bgColorStyle)s>
            <div class="confSubTitleContent">
                %(searchBox)s
                <div class="confSubTitle" %(textColorStyle)s>
                   <div class="datePlace">
                        <div class="date">%(confDateInterval)s</div>
                        <div class="place">%(confLocation)s</div>
                        <div class="timezone">%(timezone)s timezone</div>
                    </div>
                    <% if nowHappening: %>
                        <div class="nowHappening" %(textColorStyle)s><%= nowHappening %></div>
                    <% end %>
                    <% if onAirURL: %>
                        <div class="webcast" %(textColorStyle)s>
                            <%= _("Live webcast") %>: <a href="<%= webcastURL  %>"><%= _("view the live webcast") %></a>
                        </div>
                    <% end %>
                    <% if forthcomingWebcast: %>
                        <div class="webcast" %(textColorStyle)s>
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
    %(menu)s
    %(body)s
    </div>
</div>
