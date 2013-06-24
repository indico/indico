<%
    # We set these up here to pass to JS also
    strModifQuery = _('Modify Query')
    strHideQuery = _('Hide Modify Query')
    strNoGraphData = _('No graph data was returned by the server, please alter the date range.')
%>

<div id="statsWidgetsWrapper">
    <!-- Header -->
    <div class="statsWidget full edge">
        <div class="statsWidgetTitle">
            ${_('Selection Information')} (${report['startDate']} ${('to')} ${report['endDate']})
            <span style="float:right;padding-right:5px;">
                <span id="statsModify" class="fakeLink">${strModifQuery}</span>
            </span>
            <div style="clear:both;"></div>
        </div>
        <div class="statsWidgetContent">
            <span style="display:block;width:100%;">
                <div id="statsFilter">
                    <div class="statsFilterOption">
                        ${_('View statistics between these dates')}:
                        <input type="text"
                               class="statsDates"
                               id="statsFilterStartDate"
                               data-default="${report['startDate']}"
                               value="${report['startDate']}" />
                        ${_('to')}
                        <input type="text" class="statsDates"
                               id="statsFilterEndDate"
                               data-default="${report['endDate']}"
                               value="${report['endDate']}" />
                        <input type="hidden" id="confId" value="${report['confId']}" />
                        <input type="hidden" id="contribId" value="${report['contribId']}" />
                    </div>
                    <div class="statsFilterOption">
                    % if report['contributions']:
                    ${_('Choose Conference / Contribution')}:
                        <select id="updateContribution">
                            % for contribution in report['contributions']:
                               <%
                                    optionParams = 'value="' + contribution[0] + '"'

                                    if contribution[0] == report['contribId']:
                                        optionParams += ' selected="selected"'
                               %>
                               <option ${optionParams}>${contribution[1]}</option>
                            % endfor
                        </select>
                    % else:
                        <input type="hidden" id="updateContribution" value="None" />
                    % endif
                    </div>
                    <div class="statsFilterOption statsTopBordered">
                        <input type="button" id="updateQuery" value="${_('Update Query')}" />
                    </div>
                </div>
            </span>
        </div>
    </div>

    <div class="statsRow">

        <!-- Visitor hit rates -->
        <div class="statsWidget full edge">
            <div class="statsWidgetTitle">
                ${_('Visitor Hit Rates')}
                <span id="visitsInfoHelp" class="fakeLink">
                    ${_('(Info)')}
                </span>
            </div>
            <div class="statsWidgetContent">
                <div id="visitorChart">
                </div>
            </div>
        </div>
    </div>

    <div class="statsRow">

         <!-- Overall Statistics -->
        <div class="statsWidget small">
            <div class="statsWidgetTitle">
                ${_('Overall Statistics')}
            </div>
            <div class="statsWidgetContent">
                <div class="statsTableDivider">
                    ${_('Visitor Metrics')}:
                </div>
                <table style="padding-top:10px;">
                    <tr>
                        <td>${_('Visitors')}:</td>
                        <td>${report['metrics']['visits']}</td>
                    </tr>
                    <tr>
                        <td>${_('Unique Visitors')}:</td>
                        <td>${report['metrics']['uniqueVisits']}</td>
                    </tr>
                    <tr>
                        <td>${_('Returning Visitors')}:</td>
                        <td>${(report['metrics']['visits'] - report['metrics']['uniqueVisits'])}</td>
                    </tr>
                    <tr>
                        <td>${_('Avg. Duration')}:</td>
                        <td>${report['metrics']['visitLength']}</td>
                    </tr>
                </table>
                <div class="statsTableDivider">
                    ${_('Peak Statistics')}:
                </div>
                <table>
                    <tr>
                        <td>${_('Peak Date')}:</td>
                        <td>${report['metrics']['peakDate']['date']}</td>
                    </tr>
                    <tr>
                        <td>${_('Peak Users')}:</td>
                        <td>${report['metrics']['peakDate']['users']}</td>
                    </tr>
                </table>
            </div>
        </div>

        <!-- World map hits -->
        <div class="statsWidget large edge">
            <div class="statsWidgetTitle">
                ${_('Visitors Geography')}
            </div>
            <div class="statsWidgetContent">
                <img id="graphGeography" src="${Config.getInstance().getBaseURL()}/images/loading.gif"
                     alt="${_('Visitor Origins.')}" />
            </div>
        </div>

    </div>

    <div class="statsRow">

        <!-- Top Referrers -->
        <div class="statsWidget medium">
            <div class="statsWidgetTitle">
                ${_('Top Referrers')}
            </div>
            <div class="statsWidgetContent">
                <div class="statsTableDivider">
                    ${_('Traffic Inbound Top 10')}:
                </div>
                <table>
                <tr>
                    <td width="150">${_('Referrer')}</td>
                    <td>${_('Visits')}</td>
                    <td>${_('Actions')}</td>
                    <td>${_('Visit Length')}</td>
                </tr>
                % for referrer in report['metrics']['referrers']:
                <tr>
                    <td>${referrer['label']}</td>
                    <td>${referrer['nb_visits']}</td>
                    <td>${referrer['nb_actions']}</td>
                    <td>${referrer['sum_visit_length']}</td>
                </tr>
                % endfor
                </table>
            </div>
        </div>

        <!-- User Devices -->
        <div class="statsWidget medium edge">
            <div class="statsWidgetTitle">
                ${_('User Systems')}
            </div>
            <div class="statsWidgetContent" style="text-align:center;">
                <img id="graphDevices" src="${Config.getInstance().getBaseURL()}/images/loading.gif"
                     alt="${_('Visitor Systems.')}" />
            </div>
        </div>

    </div>

    <div class="statsRow">

        <!-- File Downloads -->
        <div class="statsWidget full edge">
            <div class="statsWidgetTitle">
                ${_('Material Downloads')}
            </div>
            <div class="statsWidgetContent">
                <div id="materialTree"></div>
                <div id="materialContainer">
                    <div id="materialHeader" class="statsTableDivider">
                        ${_('Downloads for')}:
                        <span id="materialTitle">
                            ${_('No Material Selected.')}
                        </span>
                        (${_('Total: ')}<span id="materialTotalDownloads">0</span>)
                    </div>
                    <div id="materialInfo">
                        <div id='materialDownloadChart'>
                            ${_('No Material Selected.')}
                        </div>
                    </div>
                </div>
            </div>
        </div>

    </div>

    <div id="statsGenerated">
        ${_('This report was generated at: %s') % formatDateTime(report['dateGenerated'], format='long')}
    </div>

    <div id="statsInfoHidden">
        ${_("Please note, statistics have only been collected since the plugin's " \
        "introduction. This means that there is no data present for the earlier " \
        "period of some events, this does not necessarily mean that there was no "\
        "activity in the event at that time.")}
    </div>
</div>

<!--  Container for popup content -->
<div style="display:none; visibility: false;">
    <div id='dialogNoGraphData' title="${_('Unable to Retrieve Graph Data')}">
        <p>
            ${_("The server did not respond in a timely manner, " \
                "it may be the case that the date-range is too large.")}
        </p>
    </div>
</div>

<script type="text/javascript">
/* i18n'd strings for statistics.js */
var str_modif_query = '${strModifQuery}';
var str_hide_query = '${strHideQuery}';

/* Data for jqPlot. */
var reportDates = {'start': "${report['startDate']}", 'end': "${report['endDate']}"};

</script>
