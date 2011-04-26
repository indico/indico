<% import MaKaC.common.Configuration as Configuration %>
<div class="container" style="max-width: 700px;">
    <div class="groupTitle">
        ${ _("About Indico") }
    </div>


    <div class="indicoHelp" style="width: 600px;">

        <div style="margin: 20px 0 10px 0;">
            <em>${ _("Indico is a free software tool that allows you to manage complex conferences, workshops and meetings.") }</em>
        </div>

        <div class="title">${ _("The Indico project") }</div>

        <div class="content" style="margin-bottom: 10px;">
        <p>${ _("""The Indico (Integrated Digital Conferencing) Project was born as a European project,
        a joint initiative of CERN, SISSA, University of Udine, TNO, and Univ. of Amsterdam.
        The main objective was to create a web-based, multi-platform conference storage and
        management system. This software would allow the storage of documents and metadata
        related to real events.""") }</p>

        <p>${ _("""Indico is currently intensively used at CERN. Most of the events that
        take place in the organization are scheduled through Indico, so that the whole community can
        consult them and collaborate. Things such as section/group meetings are easily manageable,
        allowing the participants to submit materials and share them with others. Many other events
        (mainly conferences) which happen to take place outside CERN are currently hosted in
        CERN's Indico server.""") }</p>

        </div>



        <div class="title">${ _("Features")}</div>

        <div class="content" style="margin-bottom: 10px;">

        <p>${ _("""Indico provides features for the management of the entire conference lifecycle, as well
        as for meetings and single lectures:""") }</p>
        <ul>
            <li>${ _("""Tree-like structure, organized into categories. Each category may either
            contain other categories, or contain simple events.""") }</li>

            <li>${ _("Automatic web page creation for the events.") }</li>

            <li>${ _("Event evaluation surveys.") }</li>

            <li>${ _("""Automatic notifications (i.e., automatically remembering all the participants in
            a meeting that it will take place today);""") }</li>

            <li>${ _("For Conferences:") }
                <ul>
                    <li>${ _("Registration form customization.") }</li>
                    <li>${ _("On-line payment support.") }</li>
                    <li>${ _("Abstract submission and reviewing.") }</li>
                    <li>${ _("Paper submission and reviewing.") }</li>
                </ul>
            </li>

            <li>${ _("Besides these basic features, Indico provides as well:") }
                <ul>
                    <li>${ _("""An integrated room booking system, extensible, and currently in use at CERN
                    (replacing the old CERN Room Booking System).""") }</li>
                    <li>${ _("Integrated support for videoconferencing software (i.e. VRVS11).") }</li>
                    <li>${ _("Exportation of information in different formats: RSS feeds, iCal and MARCXML, for instance.") }</li>
                    <li>${ _("Multilingual interface (internationalization).") }</li>
                    <li>${ _("Support for different time zones.") }</li>
                    <li>${ _("Accessible and usable interface.") }</li>
                </ul>
        </div>

        <div class="title">${ _("Distribution") }</div>

        <div class="content" style="margin-bottom: 10px;">
            <p>${ _("""Indico is Free Software, released under the GNU General Public License. This has
            made possible the adoption of the tool by several institutions around the world, and the
            contribution of code by third-party developers. There's an active user community, which
            almost every day provides new suggestions and bug reports. This contributes substantially to
            the degree of agility at which the Indico project currently works, providing
            immediate bug fixes, patches, and user support.</p>
            <p>As of now, besides CERN, more than 90 known instances of Indico exist, in institutions
            like Fermilab (Chicago, USA), IN2P3 (France), EPFL (Lausanne, Switzerland) and the Chinese
            Academy of Science.""") }</p>
        </div>

        <div class="title">${ _("Find more information") }</div>

        <div class="content" style="margin-bottom: 10px;">
            <p>${ _("Indico project site:") } <a href="http://indico-software.org">http://indico-software.org</a></p>

        </div>

        % if Configuration.Config.getInstance().getVersion() != "0" and Configuration.Config.getInstance().getVersion() != "":
            <div class="title">${ _("Version") }</div>

            <div class="content" style="margin-bottom: 10px;">
                <p>The version of this Indico installation is:  <em>${ Configuration.Config.getInstance().getVersion() }</em> </p>
            </div>
        % endif

    </div>

</div>
