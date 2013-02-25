<a class="right header-aligned icon-file-pdf i-button icon-only" aria-hidden="true" href="${pdf_url}" title="${_("Download PDF")}"></a>
<h2 class="page_title">${ _("Scientific Programme")}</h2>

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
