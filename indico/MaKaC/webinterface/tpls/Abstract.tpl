<%page args="abstract, display"/>
<%
from MaKaC.webinterface.common.abstractStatusWrapper import AbstractStatusList
import MaKaC.review as review
from indico.util.date_time import format_date
from MaKaC.common import Config
from indico.util.i18n import i18nformat
%>
<% s=abstract.getCurrentStatus() %>
<% comments = "" %>
<% accTrack,accType="&nbsp;","&nbsp;" %>
% if abstract.getRating() == None:
    <% rating = "-"  %>
    <% detailsImg = "" %>
% else:
    <%  questionNames = abstract.getQuestionsAverage().keys() %>
    <%  answers = abstract.getQuestionsAverage().values() %>
    <%  rating = "%.2f" % abstract.getRating() %>
    <%  imgIcon = Config.getInstance().getSystemIconURL("itemCollapsed") %>
    <%  detailsImg = """<img src="%s" onClick = "showQuestionDetails(%s,%s)" style="cursor: pointer;">"""% (imgIcon, questionNames, ["%.2f" % i for i in answers]) %>
% endif

<tr id="abstracts${abstract.getId()}" class="abstract">
    <td><input type="checkbox" name="abstracts" value="${abstract.getId()}"></td>
      % if "ID" in display:
        <td class="CRLabstractLeftDataCell">
          ${abstract.getId()}
          % if abstract.getComments():
            <img src="${systemIcon("comments")}" alt="${_("The submitter filled some comments")}" />
          % endif
        </td>
      % endif
    <td class="CRLabstractDataCell">
        <a href="${str(urlHandlers.UHCFAAbstractManagment.getURL(abstract))}">${self_.htmlText(abstract.getTitle())}</a>
    </td>
    % if "PrimaryAuthor" in display:
    <td class="CRLabstractDataCell">
      % for auth in abstract.getPrimaryAuthorList():
        % if auth.getFullName():
          ${auth.getFullName()}<br/>
        % endif
      % endfor
    </td>
    % endif
    % if "Tracks" in display:
        <% tracks = [ self_.htmlText(track.getCode() or track.getId()) for track in abstract.getTrackListSorted()] %>
        <td class="CRLabstractDataCell">${"<br>".join(tracks) or "&nbsp;"}</td>
    % endif
    % if "Type" in display:
        <td class="CRLabstractDataCell">${self_.htmlText(abstract.getContribType().getName()) if abstract.getContribType() else _("None")}</td>
    % endif
    % if "Status" in display:
        <% status=AbstractStatusList.getInstance().getCode(s.__class__ ) %>
        <% statusIconURL=AbstractStatusList.getInstance().getIconURL(s.__class__) %>
        <td class="CRLabstractDataCell" nowrap>
            <img src="${str(statusIconURL)}" border="0" alt="">${status}</td>
    % endif
    % if "Rating" in display:
        <td class="CRLabstractDataCell">${rating}&nbsp;${detailsImg}</td>
    % endif
    % if "AccTrack" in display:
        <td class="CRLabstractDataCell">${getAccTrack(abstract)}</td>
    % endif
    %if "AccType" in display:
       <td class="CRLabstractDataCell">${getAccType(abstract)}</td>
    % endif
    % if "SubmissionDate" in display:
        <td class="CRLabstractDataCell" nowrap>${format_date(abstract.getSubmissionDate(), format='long')}</td>
    % endif
    % if "ModificationDate" in display:
       <td class="CRLabstractDataCell" nowrap>${format_date(abstract.getModificationDate(), format='long')}</td>
    % endif
</tr>
