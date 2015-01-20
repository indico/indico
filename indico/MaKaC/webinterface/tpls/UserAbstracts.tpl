<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
    % if abstracts:
    <div style="border-bottom: 1px solid #EAEAEA; padding-bottom: 5px; margin-bottom: 15px;">
        <a href="${urlHandlers.UHUserAbstractsPDF.getURL(conf)}">${ _("Export to PDF")}</a>
    </div>

    <div id="abstractList">
        % for abstract in abstracts:
        <div class="abstractListAbstractItem">
            <div>
                <a href="${str( urlHandlers.UHAbstractDisplay.getURL( abstract ))}" style="font-size:14px">${abstract.getTitle()} </a>
            </div>
            <div style="line-height:17px; font-size: 12px; color:#666666;">
                <div style="display:inline"><span style="font-weight:bold">${_("Id")}: </span>${abstract.getId()}</div>
                <div style="display:inline"><span style="font-weight:bold">${_("Status")}: </span>${getAbstractStatus(abstract)}</div>
                <div style="display:inline"><span style="font-weight:bold">${_("Last modified")}: </span>${formatDate(abstract.getModificationDate()) + " "+ formatTime(abstract.getModificationDate())}</div>
            </div>
        </div>
        % endfor
    </div>
    % else:
    <p>
        ${_('There are currently no abstracts submitted for this conference.')}
    </p>
    % endif
</%block>
