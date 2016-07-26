<%from MaKaC.webinterface import urlHandlers %>
<div class="main-breadcrumb" ${'style="background-color: '+ bgColor +';" ' if bgColor else ""}>
    <span class="path">
        <a href="${ url_for_index() }">
            ${ _("Home") }
        </a>
       <span class="sep">»</span>

        <a href="${ urlHandler(**pars)  if urlHandler else "#"}">
            ${ title }
        </a>
    </span>
</span>
</div>
