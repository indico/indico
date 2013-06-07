<%inherit file="ConfDisplayBodyBase.tpl"/>

<%block name="title">
    ${body_title}
</%block>

<%block name="content">
    <div class="confDisplaySuccessMessage">
        <div class="messageText">${_("Evaluation stored. Thanks for your participation!")}</div>
    </div>

    % if redirection != None:
        <script type="text/javascript">
            function redirUrl() { return "${redirection}"; }
            document.writeln("<input class='btn' type='button' value='OK' onclick='self.location.href=redirUrl()'/>");
        </script>
        <noscript>
            <a href="${redirection}">[ OK ]</a>
        </noscript>
    % endif
</%block>
