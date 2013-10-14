<div class="tabbable tabs-left">
    <ul class="nav nav-tabs">
        {% for tab in section.tabs %}
            <li>
                <a data-toggle="tab" id="tab-{{ tab.id }}" ref="#div-{{ tab.id }}">{{ tab.name }}</a>
            </li>
        {% endfor %}
    </ul>
    <div class="tab-content regFormDialogTabContent" style="width: {{ contentWidth }}px; overflow: hidden; white-space: nowrap;">
        {% for tab in section.tabs %}
            <div class="tab-pane" id="div-{{ tab.id }}">
                {{ getTabHtml(tab) }}
            </div>
        {% endfor %}
    </div>
</div>
