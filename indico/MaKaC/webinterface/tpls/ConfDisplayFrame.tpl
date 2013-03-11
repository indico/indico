<%
if bgColorCode:
    bgColorStyle = """ style="background: #%s; border-color: #%s;" """%(bgColorCode, bgColorCode)
else:
    bgColorStyle = ""

if textColorCode:
    textColorStyle = """ style="color: #%s;" """%(textColorCode)
else:
    textColorStyle = ""
%>


<div class="conf clearfix" itemscope itemtype="http://schema.org/Event">
    <div class="confheader clearfix" ${ bgColorStyle }>
        <div class="confTitleBox" ${ bgColorStyle }>
            <div class="confTitle">
                <h1>
                    <a href="${ displayURL }">
                        <span class="conferencetitlelink" ${textColorStyle}>
                            % if logo :
                                <div class="confLogoBox">
                                   ${ logo }
                                </div>
                            % endif
                            <span itemprop="title">${ confTitle }</span>
                        </span>
      </a>
                </h1>
           </div>
        </div>
        <div class="confSubTitleBox" ${ bgColorStyle }>
            <div class="confSubTitleContent">
                ${ searchBox }
                <div class="confSubTitle" ${ textColorStyle }>
                   <div class="datePlace">
                        <div class="date">${ confDateInterval }</div>
                        <div class="place">${ confLocation }</div>
                        <div class="timezone">${ timezone } timezone</div>
                    </div>
                    % if nowHappening:
                        <div class="nowHappening" ${ textColorStyle }>${ nowHappening }</div>
                    % endif
                    % if onAirURL:
                        <div class="webcast" ${ textColorStyle }>
                            ${ _("Live webcast") }: <a href="${ webcastURL  }">${ _("view the live webcast") }</a>
                        </div>
                    % endif
                    % if forthcomingWebcast and webcastURL:
                        <div class="webcast" ${ textColorStyle }>
                            ${ _("Webcast") }:${ _(" Please note that this event will be available live via the") }
                            <a href="${ webcastURL }">${ _("Webcast Service") }</a>.
                        </div>
                    % endif
                </div>
            </div>
        </div>
        % if simpleTextAnnouncement:
            <div class="simpleTextAnnouncement">${ simpleTextAnnouncement }</div>
        % endif
    </div>
    <div id="confSectionsBox" class="clearfix">
    ${ menu }
    ${ body }
    </div>
</div>
