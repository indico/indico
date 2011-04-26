<input ${'foo'}/>

${""}

<%page args="test=None"/>
<%include file="includee.tpl"/>

Hello there!

<strong>42</strong>

% if someTest():
    <b>test succeeded</b>
% else:
    <span>failed</span>
% endif

<div class="\
%if foobar:
foo\
% else:
bar\
%endif
">

${" "}

% if "do not translate this string" == foobar:
    <br/>
% endif

% for i in xrange(1, 10):
<input type="submit" value="${"number %s" % i}"/>
% endfor

<%def name="test()">
test
</%def>

${'foo' if isFoo() else '''bar'''}
${"""bar""" if isBar() else "foo"}

<%
   for i in xrange(1, 11):
       print "Time left: %s" % i
   var = """Go1!
   Go2!
   Go3!"""
   print var
%>
