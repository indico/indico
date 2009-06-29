<xsl:stylesheet version='1.0' 
   xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:template match="/collection">
<table width="100%">
<xsl:for-each select="./agenda_item">
<xsl:sort select="./start_date" order="descending"/>
<xsl:sort select="./start_time" order="descending"/>
<xsl:apply-templates select="."/>
</xsl:for-each>
</table>
</xsl:template>

<xsl:template match="agenda_item">
<tr>
  <td width="80"><xsl:value-of select="start_date"/></td>
  <td width="50"><xsl:value-of select="start_time"/></td>
  <td><a href="http://indico.cern.ch/event/{./id}"><xsl:value-of select="title"/></a></td>
</tr>
</xsl:template>

</xsl:stylesheet>
