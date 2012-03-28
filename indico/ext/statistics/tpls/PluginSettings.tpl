<div>
    <h2>${_('This statistics plugin acts only on Conferences, Meetings and Contributions.')}</h2>
    ${_('It is not designed to provide general Analytics across the whole of ' +
    'Indico, indeed this functionality is implemented in the Services page, ' +
    'under the header Analytics.')}
    <h2>${_('Global Plugin Options')}</h2>
    <ul>
        <li>${_('Enable report caching')}: ${_('All created reports are cached ' +
        'upon creation and will not be updated until the cache has expired.')}</li>
        <li>${_('Report caching TTL')}: ${_('The time in which cached reports ' +
        'remain valid, in seconds.')}
    </ul>
</div>