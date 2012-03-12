<%page args="extargs"/>

% if extargs['trackingActive']:
    % for hook in extargs['trackingHooks']:
        <%include file="${hook.path}" args="hook=hook"/>
    % endfor
% endif