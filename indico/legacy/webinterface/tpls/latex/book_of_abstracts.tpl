<%inherit file="contribution_list_boa.tpl" />

<%block name="document_class">
    \documentclass[a4paper, 11pt, twoside]{book} %% document type
</%block>

<%block name="header_extra">
    ${parent.header_extra()}
    <%include file="inc/toc_definitions.tpl" />
</%block>

<%block name="first_page">
    <%include file="inc/first_page.tpl" args="event=conf.as_event,title=_('Book of Abstracts'),show_dates=True"/>
</%block>

<%block name="table_of_contents">
    %% TOC
    \tableofcontents
</%block>

<%block name="book_body">
    % for contrib in contribs:
        % if contrib.can_access(_session.user):
            \fancyhead[L]{\small \rmfamily \color{gray} \truncateellipses{${conf.as_event.title | latex_escape}}{300pt} / ${_("Book of Abstracts") | latex_escape}}
            \fancyhead[R]{}

            \phantomsection
            \addcontentsline{toc}{chapter}{${contrib.title | latex_escape} ${('{0}').format(contrib.friendly_id) if show_ids else ''}
            }

            <%include file="inc/contribution_condensed.tpl" args="contrib=contrib"/>
            \vspace{3em}


            \fancyfoot[C]{\small \rmfamily \color{gray} ${ latex_escape(_("Page {0}"), ignore_braces=True).format(r"\thepage") }}
        %endif
    % endfor
</%block>
