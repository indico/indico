<%from MaKaC.webinterface import urlHandlers %>
<div class="mainBreadcrumb" ${'style="background-color: '+ bgColor +';" ' if bgColor else ""}>
<span class="path">
    <a href="${ urlHandlers.UHWelcome.getURL() }">
        ${ _("Home") }
    </a>
   <img src="${ systemIcon( "breadcrumb_arrow.png" ) }" />
</span>

    <a href="${ urlHandler(**pars)  if urlHandler else "#"}">
        ${ title }
    </a>
</span>
</div>
