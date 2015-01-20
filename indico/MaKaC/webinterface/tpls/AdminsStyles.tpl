  <table class="groupTable" style="text-align: left; width: 100%;" border="0" cellpadding="0">
    <tbody>
      <tr>
        <td colspan="1" class="groupTitle">${ _("Available Styles")}
          ${inlineContextHelp(contextHelpText)}
        </td>
      </tr>
      <tr>
        <td>
          <form action="${ urlHandlers.UHAdminsAddStyle.getURL() }" method="POST">
          <input type="submit" class="btn" value="${ _("New")}">
          </form>
          <table cellspacing="1" align="center">
          <tr style="border-bottom: 1px;">
            <th>${ _("Name")}</th>
            <th>${ _("ID")}</th>
            <th>${ _("Files")}</th>
            <th>${ _("Actions")}</th>
          </tr>
          <% styles = styleMgr.getStyles().keys() %>
          <% styles.sort() %>
          % for style in styles:
          <tr style="background-color: ${"#faa" if not styleMgr.isCorrectStyle(style) else "lightgreen"}">
            <td align="left">${ styleMgr.getStyleName(style) }</td>
            <td align="left">${style}</td>
            <td align="left">
            % if style == 'static':
                -
            % else:
                ${styleMgr.getTemplateFilename(style)} ${"(not found)" if not styleMgr.existsTPLFile(style) and not styleMgr.existsXSLFile(style) else ""}<br/>
                % if styleMgr.getCSSFilename(style) != None:
                    ${styleMgr.getCSSFilename(style)} ${"(not found)" if not styleMgr.existsCSSFile(style) else ""}
                % else:
                    <em>(CSS is not used for this style)</em>
                % endif
            % endif
            </td>
            <td>
            % if style == "static":
            ${inlineContextHelp(_('This style cannot be deleted. This is the default style for conferences.'))}
            % else:
            <a href="${urlHandlers.UHAdminsDeleteStyle.getURL(templatefile=style)}"
               data-confirm='${_("Are you sure you want to delete this style?")}' data-title='${_("Delete style")}'>
              <img border="0" src="${deleteIconURL}" alt="${ _("delete this style")}"/>
            </a>
            % endif
            </td>
          </tr>
          % endfor
          </table>
        </td>
      </tr>

      <% types = (("simple_event", _("Styles for Lectures")),
                  ("meeting",      _("Styles for Meetings")),
                  ("conference",   _("Styles for Conferences")))%>
      % for eventType, groupTitle in types:
      <tr>
        <td colspan="1" class="groupTitle">${groupTitle}</td>
      </tr>
      <tr>
        <td>
          <form action="${ urlHandlers.UHAdminsStyles.getURL() }" method="POST">
          <input type="hidden" name="event_type" value="${eventType}">
          <% styles = styleMgr.getStyleListForEventType(eventType) %>
          <% styles.sort() %>
          ${ _("current list:")} <select name="tplfile">
          % for style in styles:
          <% isDefault = style.strip() == styleMgr.getDefaultStyleForEventType(eventType).strip() %>
          <option value="${style}"${'style="font-weight: bold;" selected' if isDefault else ""}>${styleMgr.getStyleName(style)}${" (default)" if isDefault else ""}</option>
          % endfor
          </select>
          <input type="submit" class="btn" name="action" value="${ _("default")}">
          <input type="submit" class="btn" name="action" value="${ _("delete")}"><br>
          ${ _("add new style:")}
           <select name="newstyle">
             % for style in styleMgr.getStyles():
               % if style not in styles:
               <option value="${ style }">${styleMgr.getStyleName(style)}</option>
               % endif
             % endfor
           </select>
           <input type="submit" class="btn" name="action" value="${ _("add")}">
          </form>
        </td>
      </tr>
      % endfor
    </tbody>
  </table>
