<table>
    <thead>
        <tr role="rowheader">
            {% if config.actions.indexOf("sortable") > -1 %}
                <th></th>
            {% endif %}
            {% for el in config.colNames %}
                <th style="width: {{config.colModel[loop.index0].width}}px;">{{ el }}</th>
            {% endfor %}
        </tr>
    </thead>
</table>
