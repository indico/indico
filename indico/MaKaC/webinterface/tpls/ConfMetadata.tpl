% if site_name == 'Indico':
    <meta property="og:site_name" content="Indico">
% else:
    <meta property="og:site_name" content="Indico - ${site_name}">
% endif
<meta property="og:type" content="event" />
% if social.get('facebook_app_id'):
    <meta property="fb:app_id" content="${social['facebook_app_id']}">
% endif
<meta property="og:image" content="${image}"/>
<meta property="og:description" content="${description|h}"/>
