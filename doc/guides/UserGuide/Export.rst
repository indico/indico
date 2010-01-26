=====================
Exporting Indico Data
=====================

To Personal Scheduler Tools (Outlook, iCal, korganizer...)
----------------------------------------------------------

You can export an event or a set of events to your personal
scheduler tool by using the Indico iCal export. When you see
this icon |image162|, the link *iCal export*, or the menu *More*
> *Export to Ical*, you can click on it to export the content of
the page you are on to your scheduler tool.

On an event page, the event will be exported, on a category page,
all events in the category will be exported. Some scheduler tools
recognize multiple events (iCal, korganizer, Outlook 2007),
others do not (Outlook 2003), in this case only the first event in
the list is recognized.

You can also ask your personal scheduler tool to subscribe to one
of these export URLs (this is particularly interesting for the
Category export). For iCal: "Calendar" menu -> menu item
"Subscribe", then enter the URL of the iCal export. Finally, set the
"Refresh" to "Every day". Every day, your iCal software will update
its content with any new event in the Category.

--------------

RSS feeds
---------

Indico provides RSS feeds on each Category page. If your browser
is RSS-aware, you will see an icon like this on the browser menu
bar: |image163|. Click on it to access the RSS feed, and 
subscribe to it using an RSS aggregator.

--------------

Sharepoint
----------

If you maintain a Sharepoint web site, it is very easy to create
inside it a web part exposing the forthcoming events from an Indico
category. First add an XML web part, then in the "XML link" part,
add the `XML export <#using-the-export.py-script>`_ URL from indico (eg.
http://indico.cern.ch/tools/export.py?fid=2l12&date=today&days=1000&of=xml)
and in the "XSL link" part, add this URL:
http://indico.cern.ch/export.xsl.

The result should look like this:

|image164|

--------------

Using the export.py script
--------------------------

Indico allows you to programmatically access the content of its
database by exposing its events through a web service, the
export.py script.

A typical example of how to use this script is:

http://my.indico.server/tools/export.py?fid=2l12&date=today&days=1000&of=xml

where:

* *fid* is the category from which you want to extract the events (can be a *+* separated list)
* *date* is the starting date of the event (format: *yyyy-mm-dd* or *today*)
* *days* is the number of days to export the events (starting on *date*)
* *of* is the output format (one of *xml*, *html*, *ical*, *rss*)
        

--------------

.. |image162| image:: UserGuidePics/ical_small.png
.. |image163| image:: UserGuidePics/rss.png
.. |image164| image:: UserGuidePics/sharepoint.png
