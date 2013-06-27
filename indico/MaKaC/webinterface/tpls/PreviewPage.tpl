<div class="cssTplSelection">
    <form action="${ saveCSS }" method="POST" ENCTYPE="multipart/form-data">
        <label for="demo">${ _("Select to switch templates")}</label>
        <select id="selectedTpl" name="selectedTpl">
        % for tpl in templatesList:
            <% selectedV = "" %>
            % if tpl.getId() == selectedCSSId:
                <% selectedV = """ selected="selected" """%>
            % endif
            <option value="${ tpl.getId() }"${ selectedV }>${ tpl.getFileName(extension=False) }</option>
        % endfor
        </select>
        <script>
            $('#selectedTpl').on('change', function() {
                location.href = build_url('${ previewURL }', {
                    cssId: $(this).val()
                });
            });
        </script>
        <input type="submit" class="btn" value="${ _("Take template in use")}">
        <br/>
        % if cssurl:
        <a id="css_download" rel="attachment follow" title="${ _("Download template for modification")}" href="${ cssurl }">${ _("Download css")}</a>
        <br/>
        % endif
        <a href="${ URL2Back }">${ _("Back to management area")}</a>
    </form>
</div>

${ bodyConf }
