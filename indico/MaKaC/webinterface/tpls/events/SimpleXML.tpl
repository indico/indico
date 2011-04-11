<% import lxml.etree %>
<pre>${ lxml.etree.tostring(iconf, pretty_print=True) | h }</pre>