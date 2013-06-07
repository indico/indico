<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="toolbar">
    <a class="i-button icon-file-pdf icon-only" aria-hidden="true" href="${pdf_url}" title="${_("Download PDF")}"></a>
</%block>

<%block name="content">
    <div class="quotation programme">
        ${ description }
    </div>

    <ul class="programme">
        % for track in program:
            <li>
              % if 'url' in track:
              <a class="right" href='${track['url']}'>edit</a>
              % endif
              <span class="title">${track['title']}</span>
              <div class="description">
                ${track['description']}
              </div>
            </li>
        % endfor
    </ul>
</%block>
