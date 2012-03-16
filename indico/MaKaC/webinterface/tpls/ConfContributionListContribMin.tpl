<%page args="contrib=None"/>

<tr>
    <td>
        <input type="checkbox" name="contributions" value="contrib.getId()">
    </td>
    <td class="abstractDataCell"></td>
    <td class="abstractDataCell"></td>
    % if len(conf.getContribTypeList()) > 0:
        <td class="abstractDataCell"></td>
    % endif
    <td class="abstractDataCell">
        <a href="${str( urlHandlers.UHContributionDisplay.getURL( contrib ))}">${contrib.getTitle()}</a>
    </td>
    <td class="abstractDataCell"></td>
    <td class="abstractDataCell"></td>
    % if len(conf.getTrackList()) > 0:
        <td class="abstractDataCell"></td>
    % endif
    <td class="abstractDataCell">
        % if contrib.getSlides():
            % if contrib.getSlides().canView(accessWrapper):
                <img src="${Config.getInstance().getSystemIconURL('slides')}" alt="${_('Slides')}" border="0"/>
            % endif
        % endif
        % if contrib.getPaper():
            % if contrib.getPaper().canView(accessWrapper):
                <img src="${Config.getInstance().getSystemIconURL('paper')}" alt="${_('Paper')}" border="0"/>
            % endif
        % endif
    </td>
    <td class="abstractDataCell">
        % if conf.getAbstractMgr().showAttachedFilesContribList() and isinstance(contrib, conference.AcceptedContribution) and len(contrib.getAbstract().getAttachments()) > 0:
            % for file in contrib.getAbstract().getAttachments().values():
                <div style="padding-bottom:3px;">
                    <a href="${str(urlHandlers.UHAbstractAttachmentFileAccess.getURL(file))}">${file.getFileName()}</a>
                </div>
            % endfor
        % endif
    </td>
</tr>