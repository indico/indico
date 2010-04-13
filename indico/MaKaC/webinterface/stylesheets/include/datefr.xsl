<?xml version='1.0'?>
<!--

     This file is part of CDS Indico.
     Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.

     CDS Indico is free software; you can redistribute it and/or
     modify it under the terms of the GNU General Public License as
     published by the Free Software Foundation; either version 2 of the
     License, or (at your option) any later version.

     CDS Indico is distributed in the hope that it will be useful, but
     WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
     General Public License for more details.

     You should have received a copy of the GNU General Public License
     along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
     59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
-->

<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:date="http://exslt.org/dates-and-times"
                xmlns:func="http://exslt.org/functions"
                extension-element-prefixes="date func">

<xsl:param name="date:date-time" select="'2000-01-01T00:00:00Z'" />

<date:month-lengths>
   <date:month>31</date:month>
   <date:month>28</date:month>
   <date:month>31</date:month>
   <date:month>30</date:month>
   <date:month>31</date:month>
   <date:month>30</date:month>
   <date:month>31</date:month>
   <date:month>31</date:month>
   <date:month>30</date:month>
   <date:month>31</date:month>
   <date:month>30</date:month>
   <date:month>31</date:month>
</date:month-lengths>

<date:days>
   <date:day abbr="Dim">Dimanche</date:day>
   <date:day abbr="Lun">Lundi</date:day>
   <date:day abbr="Mar">Mardi</date:day>
   <date:day abbr="Mer">Mercredi</date:day>
   <date:day abbr="Jeu">Jeudi</date:day>
   <date:day abbr="Ven">Vendredi</date:day>
   <date:day abbr="Sam">Samedi</date:day>
</date:days>

<func:function name="date:day-name">
	<xsl:param name="date-time">
      <xsl:choose>
         <xsl:when test="function-available('date:date-time')">
            <xsl:value-of select="date:date-time()" />
         </xsl:when>
         <xsl:otherwise>
            <xsl:value-of select="$date:date-time" />
         </xsl:otherwise>
      </xsl:choose>
   </xsl:param>
   <xsl:variable name="neg" select="starts-with($date-time, '-')" />
   <xsl:variable name="dt-no-neg">
      <xsl:choose>
         <xsl:when test="$neg or starts-with($date-time, '+')">
            <xsl:value-of select="substring($date-time, 2)" />
         </xsl:when>
         <xsl:otherwise>
            <xsl:value-of select="$date-time" />
         </xsl:otherwise>
      </xsl:choose>
   </xsl:variable>
   <xsl:variable name="dt-no-neg-length" select="string-length($dt-no-neg)" />
   <xsl:variable name="timezone">
      <xsl:choose>
         <xsl:when test="substring($dt-no-neg, $dt-no-neg-length) = 'Z'">Z</xsl:when>
         <xsl:otherwise>
            <xsl:variable name="tz" select="substring($dt-no-neg, $dt-no-neg-length - 5)" />
            <xsl:if test="(substring($tz, 1, 1) = '-' or 
                           substring($tz, 1, 1) = '+') and
                          substring($tz, 4, 1) = ':'">
               <xsl:value-of select="$tz" />
            </xsl:if>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:variable>
   <xsl:variable name="day-of-week">
      <xsl:if test="not(string($timezone)) or
                    $timezone = 'Z' or 
                    (substring($timezone, 2, 2) &lt;= 23 and
                     substring($timezone, 5, 2) &lt;= 59)">
         <xsl:variable name="dt" select="substring($dt-no-neg, 1, $dt-no-neg-length - string-length($timezone))" />
         <xsl:variable name="dt-length" select="string-length($dt)" />
         <xsl:variable name="year" select="substring($dt, 1, 4)" />
         <xsl:variable name="leap" select="(not($year mod 4) and $year mod 100) or not($year mod 400)" />
         <xsl:variable name="month" select="substring($dt, 6, 2)" />
         <xsl:variable name="day" select="substring($dt, 9, 2)" />
         <xsl:if test="number($year) and
                       substring($dt, 5, 1) = '-' and
                       $month &lt;= 12 and
                       substring($dt, 8, 1) = '-' and
                       $day &lt;= 31 and
                       ($dt-length = 10 or
                        (substring($dt, 11, 1) = 'T' and
                         substring($dt, 12, 2) &lt;= 23 and
                         substring($dt, 14, 1) = ':' and
                         substring($dt, 15, 2) &lt;= 59 and
                         substring($dt, 17, 1) = ':' and
                         substring($dt, 18) &lt;= 60))">
            <xsl:variable name="month-days" select="sum(document('')/*/date:month-lengths/date:month[position() &lt; $month])" />
            <xsl:variable name="days">
               <xsl:choose>
                  <xsl:when test="$leap and $month > 2">
                     <xsl:value-of select="$month-days + $day + 1" />
                  </xsl:when>
                  <xsl:otherwise>
                     <xsl:value-of select="$month-days + $day" />
                  </xsl:otherwise>
               </xsl:choose>
            </xsl:variable>
            <xsl:variable name="y-1" select="$year - 1" />
            <xsl:value-of select="(($y-1 + floor($y-1 div 4) - floor($y-1 div 100) + floor($y-1 div 400) + $days) mod 7) + 1" />
         </xsl:if>
      </xsl:if>
   </xsl:variable>
   <func:result select="string(document('')/*/date:days/date:day[number($day-of-week)])" />   
</func:function>

<date:months>
   <date:month abbr="Jan">Janvier</date:month>
   <date:month abbr="F&#xE9;v">F&#xE9;vrier</date:month>
   <date:month abbr="Mar">Mars</date:month>
   <date:month abbr="Avr">Avril</date:month>
   <date:month abbr="Mai">Mai</date:month>
   <date:month abbr="Jun">Juin</date:month>
   <date:month abbr="Jul">Juillet</date:month>
   <date:month abbr="Ao&#xFB;">Ao&#xFB;t</date:month>
   <date:month abbr="Sep">Septembre</date:month>
   <date:month abbr="Oct">Octobre</date:month>
   <date:month abbr="Nov">Novembre</date:month>
   <date:month abbr="D&#xE9;c">D&#xE9;cembre</date:month>
</date:months>

<func:function name="date:month-name">
	<xsl:param name="date-time">
      <xsl:choose>
         <xsl:when test="function-available('date:date-time')">
            <xsl:value-of select="date:date-time()"/>
         </xsl:when>
         <xsl:otherwise>
            <xsl:value-of select="$date:date-time"/>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:param>
   <xsl:variable name="neg" select="starts-with($date-time, '-') and not(starts-with($date-time, '--'))"/>
   <xsl:variable name="dt-no-neg">
      <xsl:choose>
         <xsl:when test="$neg or starts-with($date-time, '+')">
            <xsl:value-of select="substring($date-time, 2)"/>
         </xsl:when>
         <xsl:otherwise>
            <xsl:value-of select="$date-time"/>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:variable>
   <xsl:variable name="dt-no-neg-length" select="string-length($dt-no-neg)"/>
   <xsl:variable name="timezone">
      <xsl:choose>
         <xsl:when test="substring($dt-no-neg, $dt-no-neg-length) = 'Z'">Z</xsl:when>
         <xsl:otherwise>
            <xsl:variable name="tz" select="substring($dt-no-neg, $dt-no-neg-length - 5)"/>
            <xsl:if test="(substring($tz, 1, 1) = '-' or substring($tz, 1, 1) = '+') and substring($tz, 4, 1) = ':'">
               <xsl:value-of select="$tz"/>
            </xsl:if>
         </xsl:otherwise>
      </xsl:choose>
   </xsl:variable>
   <xsl:variable name="month">
      <xsl:if test="not(string($timezone)) or $timezone = 'Z' or (substring($timezone, 2, 2) &lt;= 23 and substring($timezone, 5, 2) &lt;= 59)">
         <xsl:variable name="dt" select="substring($dt-no-neg, 1, $dt-no-neg-length - string-length($timezone))"/>
         <xsl:variable name="dt-length" select="string-length($dt)"/>
         <xsl:choose>
            <xsl:when test="substring($dt, 1, 2) = '--' and substring($dt, 3, 2) &lt;= 12 and substring($dt, 5, 1) = '-' and (substring($dt, 6) = '-' or ($dt-length = 7 and substring($dt, 6) &lt;= 31))">
               <xsl:value-of select="substring($dt, 3, 2)"/>
            </xsl:when>
            <xsl:when test="number(substring($dt, 1, 4)) and substring($dt, 5, 1) = '-' and substring($dt, 6, 2) &lt;= 12 and ($dt-length = 7 or (substring($dt, 8, 1) = '-' and substring($dt, 9, 2) &lt;= 31 and ($dt-length = 10 or (substring($dt, 11, 1) = 'T' and substring($dt, 12, 2) &lt;= 23 and substring($dt, 14, 1) = ':' and substring($dt, 15, 2) &lt;= 59 and substring($dt, 17, 1) = ':' and substring($dt, 18) &lt;= 60))))">
               <xsl:value-of select="substring($dt, 6, 2)"/>
            </xsl:when>
         </xsl:choose>
      </xsl:if>
   </xsl:variable>
   <func:result select="string(document('')/*/date:months/date:month[number($month)])"/>
</func:function>

<xsl:template name="prettydate">
	<xsl:param name="dat" select="0"/>
	<xsl:value-of select="date:day-name($dat)"/>
	<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
	<xsl:value-of select="substring($dat,9,2)"/>
	<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
	<xsl:value-of select="date:month-name($dat)"/>
	<xsl:text disable-output-escaping="yes">&#38;nbsp;</xsl:text>
	<xsl:value-of select="substring($dat,1,4)"/>
</xsl:template>


<xsl:template name="prettyduration">
	<xsl:param name="duration" select="0"/>
	<xsl:if test="number(substring($duration,1,2)) != '00'">
		<xsl:value-of select="translate(substring($duration,1,2),'0','')"/>h</xsl:if><xsl:value-of select="substring($duration,4,2)"/>'
</xsl:template>

</xsl:stylesheet>
