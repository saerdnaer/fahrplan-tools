<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE xsl:stylesheet[
   <!ENTITY br '<xsl:value-of select="$newline"/>'>
   <!ENTITY room_uri 'property:Has_session_location/@rdf:resource'>   
]>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
                xmlns:swivt="http://semantic-mediawiki.org/swivt/1.0#"
                xmlns:property="http://events.ccc.de/congress/2014/wiki/Special:URIResolver/Property-3A">
  <xsl:output method="xml" indent="yes" />
  <!--xsl:strip-space elements="*" /-->
  <!--xsl:preserve-space elements="*" /-->

<xsl:key name="days" match="/rdf:RDF/swivt:Subject" use="substring-before(property:Has_start_time, 'T')"/>
<!--xsl:key name="rooms" match="/rdf:RDF/swivt:Subject" use="&room_uri;"/-->
<xsl:key name="rooms-by-day" match="/rdf:RDF/swivt:Subject" use="concat(substring-before(property:Has_start_time, 'T'), &room_uri;)"/>



<xsl:template match="/">
<schedule>
  <xsl:for-each select="/rdf:RDF/swivt:Subject[property:Has_start_time][generate-id() = generate-id(key('days', substring-before(property:Has_start_time, 'T'))[1])]">
  <xsl:variable name="day"><xsl:value-of select="substring-before(property:Has_start_time, 'T')"/></xsl:variable>
  <day>
    <xsl:attribute name="date"><xsl:value-of select="$day" /></xsl:attribute>
    <xsl:for-each select="/rdf:RDF/swivt:Subject[generate-id() = generate-id(key('rooms-by-day', concat($day, &room_uri;))[1])]"> <xsl:text>
    </xsl:text>
    <room>
      <xsl:variable name="room_raw"><xsl:value-of select="substring-after(&room_uri;, 'URIResolver/')"/></xsl:variable>
      <xsl:variable name="room"><xsl:value-of select="concat(substring-before($room_raw, '-3A'), ' ', substring-after($room_raw, '-3A'))"/></xsl:variable>
      <xsl:attribute name="name"><xsl:value-of select="$room"/></xsl:attribute>
      <!--<xsl:apply-templates select="key('rooms', &room_uri;)[substring-before(property:Has_start_time, 'T') = $day]" /--><xsl:text>
      </xsl:text>
      <xsl:apply-templates select="key('rooms-by-day', concat(substring-before(property:Has_start_time, 'T'), &room_uri;))" />
    </room> <xsl:text>
</xsl:text>
    </xsl:for-each>
    </day>
    </xsl:for-each>
  </schedule>
  </xsl:template>
<!--
TODO:
* Funktion für Raumname definieren.
* durch Tage itereieren
* durch Räume iterieren
* Whitespace problematik...
* sortieren

 http://www.getsymphony.com/discuss/thread/87656/
 
-->



<xsl:variable name="newline"><xsl:text>
       </xsl:text></xsl:variable>


  <!--xsl:template match="*"><xsl:apply-templates select="child::*" /></xsl:template-->

  <xsl:template match="swivt:Subject">
      <event>
        <xsl:attribute name="guid"><xsl:value-of select="substring-after(swivt:wikiPageSortKey, '# ')" /></xsl:attribute> <xsl:value-of select="$newline"/>

        <date><xsl:value-of select="property:Has_start_time"/></date> <xsl:value-of select="$newline"/>
        <start><xsl:value-of select="substring(substring-after(property:Has_start_time, 'T'), 0, 6)"/></start> <xsl:value-of select="$newline"/>
        <duration><xsl:call-template name="decimal_to_time"> 
            <xsl:with-param name="decimal" select="property:Has_duration"/>
        </xsl:call-template></duration> <xsl:value-of select="$newline"/>
        <room><xsl:value-of select="substring-after(&room_uri;, '/Room-3A')"/></room> <xsl:value-of select="$newline"/>
        <slug /> <xsl:value-of select="$newline"/>
        <recording><license/><optout/></recording> <xsl:value-of select="$newline"/>
        <title><xsl:value-of select="property:Has_event_title"/></title> <xsl:value-of select="$newline"/>
        <subtitle/> <xsl:value-of select="$newline"/>
        <track><xsl:value-of select="property:Has_event_track"/></track> <xsl:value-of select="$newline"/>
        <type>workshop</type> <xsl:value-of select="$newline"/>
        <language/> <xsl:value-of select="$newline"/>
        <abstract/> <xsl:value-of select="$newline"/>
        <description/> <xsl:value-of select="$newline"/>
        <persons/> <xsl:value-of select="$newline"/>
        <links/>

        <xsl:text>
      </xsl:text>
      </event><xsl:text>
      </xsl:text>

  </xsl:template>
  
  <xsl:template match='text()|@*' />

<xsl:template name="decimal_to_time">
<xsl:param name="decimal"/>
<xsl:value-of select="concat(
  format-number(floor($decimal div 60), '0:'),
  format-number(floor($decimal mod 60), '00'))"/>
</xsl:template>

</xsl:stylesheet>
