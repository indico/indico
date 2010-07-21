// include the Google Maps API
mapsKey = "ABQIAAAAma3utMfjLLhSmsMwYFxuOxQw5QZGSL2Qh09zAqNyDcYBVXi0OBTBnNqS2Hl5cVWGNuhE9BATvtEqyA";
include("http://maps.google.com/maps?file=api&amp;v=2&amp;key=" + mapsKey);

/**
 * A Google Map of rooms.
 */
type ("RoomMap", ["IWidget"],
    {
        initialize: function(mapCanvas, aspectsCanvas, aspects, buildings) {
            if (GBrowserIsCompatible()) {
                this.createMap(mapCanvas);
                this.createAspectChangeLinks(aspectsCanvas, aspects);
                this.createMarkers(buildings);
            } else {
                this.showNotCompatible(mapCanvas);
            }
        },

        createMap: function(mapCanvas) {
            // Google Maps API setup
            this.map = new GMap2(mapCanvas);
            this.map.setMapType(G_HYBRID_MAP);
            this.map.setUIToDefault();
            this.map.enableDoubleClickZoom();
        },

        createInfoMarker: function(point, info) {
            var marker = new GMarker(point);

            // when the marker is clicked, open the info window
            GEvent.addListener(marker, "click", function() {
                marker.openInfoWindowHtml(info);
            });

            return marker;
        },

        setSelectedAspectStyle: function(link) {
            // unselect the previous selected link (if any)
            if (this.selectedLink) {
                this.selectedLink.dom.className = 'mapAspectUnselected';
            }

            // select the clicked link
            this.selectedLink = link;
            link.dom.className = 'mapAspectSelected';
        },

        createAspectChangeFunction: function(aspect, link) {
            setSelectedAspectStyle = this.setSelectedAspectStyle;
            map = this.map;
            return function() {
                map.setCenter(new GLatLng(aspect.lat, aspect.lon), aspect.zoom);
                setSelectedAspectStyle(link);
            }
        },

        createAspectChangeLinks: function(aspectsCanvas, aspects) {
            var links = Html.ul({className:'mapAspectsList'}).dom;
            for (var i = 0; i < aspects.length; i++) {
                aspect = aspects[i];

                // construct a link that changes the map aspect if clicked
                var link = Html.a({'href':'#', className:'mapAspectUnselected'}, aspect.name);
                var itemClassName = i == 0 ? 'first' : i == aspects.length - 1 ? 'last' : '';
                var item = Html.li({className:itemClassName}, link.dom);
                var aspectChangeFunction = this.createAspectChangeFunction(aspect, link);

                // if the aspect is a default one, apply it on start
                if (aspect.isDefault) {
                    aspectChangeFunction();
                }

                // on click, apply the clicked aspect on the map
                link.observeClick(aspectChangeFunction);

                links.appendChild(item.dom);
            }
            aspectsCanvas.appendChild(links);
        },

        createRoomInfo: function(building, room) {
            // info format: [link with room address] - [description of the room]
            var address = building.number + '/' + room.floor + '-' + room.roomNr;
            var link = Html.a({href:room.url, className:'mapRoomLink'}, address).dom;
            var desc = Html.span({className:'mapRoomDescription'}, room.markerDescription).dom;

            roomInfo = Html.p({className:'mapRoomInfo'}, link, ' - ', desc);
            return roomInfo.dom;
        },

        createBuildingInfo: function(building) {
            // the building title
            var title = Html.p({className:'mapBuildingTitle'}, building.title).dom;

            // the div containing info about rooms
            var roomsInfo = Html.div({className:'mapRoomsInfo'}).dom;

            // add info for each room
            for (var j = 0; j < building.rooms.length; j++) {
                var room = building.rooms[j];
                var roomInfo = this.createRoomInfo(building, room);
                roomsInfo.appendChild(roomInfo);
            }

            var buildingInfo = Html.div({className:'mapBuildingInfo'}, title, roomsInfo);
            return buildingInfo.dom;
        },

        createMarkers: function(buildings) {
            for (var i = 0; i < buildings.length; i++) {
                var building = buildings[i];

                // initialize the marker aspect and info
                var pos = new GLatLng(building.latitude, building.longitude);
                var info = this.createBuildingInfo(building);

                // construct the marker and add it to the map overlay
                var marker = this.createInfoMarker(pos, info);
                this.map.addOverlay(marker);
            }
        },

        showNotCompatible: function(mapCanvas) {
            var info = Html.div({}, "Your browser is not compatible with Google Maps!").dom;
            mapCanvas.appendChild(info);
        },

    },

    /**
     * Constructor of the RoomMap
     */
    function(mapCanvas, aspectsCanvas, aspects, buildings) {
        this.initialize(mapCanvas, aspectsCanvas, aspects, buildings);
        this.values = {};
        this.extraComponents = [];
    }
);
