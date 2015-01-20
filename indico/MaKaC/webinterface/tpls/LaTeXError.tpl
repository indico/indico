<div class="container">
    <div class="error-message-box" style="max-width: 800px;">
        <div class="message-text text-left">
            % if is_manager:
                ${_("Could not generate this LaTeX document! It is possible that there are errors in some of your abstracts/contributions. Please have a look at the logs/source code below to find the faulty parts and come back to Indico to fix them.")}
                <div>
                    <h2>${_("pdflatex log")}
                        <a class="i-button icon-material-download right" style="font-size: 0.7em;"
                            href="${url_for('misc.error-report-download', report_id=report_id, filename='pdflatex.log')}">${_("Download")}</a>
                    </h2>
                    <textarea class="log" style="width: 100%; min-height: 300px;">
                        ${log}
                    </textarea>

                    <h2>${_("LaTeX source code")}
                        <a class="i-button icon-material-download right" style="font-size: 0.7em;"
                            href="${url_for('misc.error-report-download', report_id=report_id, filename='source.tex')}">${_("Download")}</a>
                    </h2>

                    <textarea class="log" style="width: 100%; min-height: 300px;">
                        ${source_code}
                    </textarea>
                </div>
            % else:
                ${_("Could not generate LaTeX document! It is possible that there are errors in the document source code. Please contact the event organiser.")}
            % endif
        </div>
    </div>
</div>