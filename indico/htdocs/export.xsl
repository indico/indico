<xsl:stylesheet version='1.0' xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="html" indent="yes"/>

  <xsl:template match="/httpapiresult">
    <xsl:apply-templates select="./results"/>
  </xsl:template>

  <xsl:template match="results">
    <xsl:if test="*">
      <table style="width: 100%;">
        <xsl:for-each select="./conference">
          <xsl:apply-templates select="."/>
        </xsl:for-each>
      </table>
    </xsl:if>
  </xsl:template>

  <xsl:template match="conference">
    <tr>
      <td style="width: 80px;"><xsl:value-of select="substring-before(startDate, 'T')"/></td>
      <td style="width: 50px;"><xsl:value-of select="substring-before(substring-after(startDate, 'T'), ':00+')"/></td>
      <td><a href="{./url}"><xsl:value-of select="title"/></a></td>
    </tr>
  </xsl:template>

</xsl:stylesheet>

