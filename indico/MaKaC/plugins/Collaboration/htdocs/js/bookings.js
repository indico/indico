var videoServiceLaunchInfo = {};

var TPL_DISPLAY_BUTTON = {
    'disconnect': function(elem) {
        elem.children(".button-text").text(format($T("Disconnect {0}"), [elem.data('location')]));
        elem.removeClass('connect_room').addClass('disconnect_room');
    },
    'connect': function(elem) {
        elem.children(".button-text").text(format($T("Connect {0}"), [elem.data('location')]));
        elem.removeClass('disconnect_room').addClass('connect_room');
    },
    'error' : function(elem, error_msg) {
        elem.css('display', 'inline-block');
        elem.text(elem.data('location'));
        elem.addClass('icon-warning');
        elem.qtip({
            content: {
                text: any(error_msg, $T("Indico cannot reach this room right now. Please reload the page to try again."))
            },
            position: {
                my: 'top center',
                at: 'bottom center'
            },
            hide: {
                fixed: true
            }
        });
    }
}

var TPL_MANAGEMENT_BUTTON = {
    'disconnect': function(elem) {
        elem.removeClass("icon-play").addClass("icon-stop").children(".button-text").text(format($T("Disconnect {0}"), [elem.data('location')]));
        elem.removeClass('connect_room').addClass('disconnect_room');
    },
    'connect': function(elem) {
        elem.removeClass("icon-stop").addClass("icon-play").children(".button-text").text(format($T("Connect {0}"), [elem.data('location')]));
        elem.removeClass('disconnect_room').addClass('connect_room');
    },
    'error' : function(elem, error_msg) {
        elem.css('display', 'inline-block');
        elem.text(elem.data('location'));
        elem.removeClass("icon-stop").removeClass("icon-play");
        elem.addClass('i-button icon-warning disabled');
        elem.qtip({
            content: {
                text: any(error_msg, $T("Indico cannot reach this room right now. Please reload the page to try again."))
            },
            position: {
                my: 'top center',
                at: 'bottom center'
            },
            hide: {
                fixed: true
            }
        });
    }
};


type("ConnectButton", [], {
    initialize: function(elem, booking, conf_id) {
        this.connected = true;
        this.error = false;
        this.error_msg = null;
        this.$el = elem;

        this.booking = booking;
        this.conf_id = conf_id;

        this.params = {
            conference: conf_id,
            bookingId: booking.id
        };

        this.connection = null;
        this.in_progress = false;

        this.$el.click(_.bind(this.on_click, this));

        this.check_room_connection();
        this.tpl = TPL_DISPLAY_BUTTON;
    },

    render: function() {
        this.hide_progress();

        if (this.error) {
            this.tpl['error'](this.$el, this.error_msg);
        } else {
            if(this.connected){
                this.tpl['disconnect'](this.$el);
            } else {
                this.tpl['connect'](this.$el);
            }
        }
    },

    set_progress: function() {
        this.in_progress = true;
        this.$el.children(".button-text").text('');
        this.$el.children(".progress").show();
        this.$el.children(".progress").html(progressIndicator(true, true).dom);
    },

    hide_progress: function() {
        this.in_progress = false;
        this.$el.children(".progress").hide();
    },

    on_click: function() {
        if (this.error) {
            return;
        } else {
            this.set_progress();

            if (this.connected) {
                this.disconnect_room();
            } else {
                this.connect_room();
            }
        }

        return false;
    },

    check_room_connection: function(on_result) {
        var self = this;
        this.$el.children(".progress").html(progressIndicator(true, true).dom);

        indicoRequest(
            'vidyo.checkVidyoBookingConnection',
            this.params,
            function(result,error) {
                if (!error) {
                    if (result.error) {
                        self.error = true;
                        self.error_msg = result.userMessage;
                        self.render()
                    } else {
                        // store connection data/status
                        self.connection = result;

                        if (result.service.toLowerCase() == self.booking.type.toLowerCase() &&
                            result.roomName == self.booking.bookingParams.roomName &&
                            result.isConnected) {
                            self.connected = true;
                        } else {
                            self.connected = false;
                        }

                        if (!self.in_progress) {
                            self.render()
                        }

                        if (on_result) {
                            _.bind(on_result, self)(result);
                        }
                    }
                } else {
                    self.error = true;
                    self.render()
                }
            });
    },

    request_room: function(method, success_msg, on_answer, on_success, on_error, extra_params) {
        var self = this;

        indicoRequest(
            method,
            _(this.params).extend(extra_params || {}),
            function(result, error) {
                if (on_answer) {
                    on_answer(result, error);
                }

                if (!error) {
                    if (result.error){
                        new WarningPopup($T("Operation failed"), result.userMessage).open();

                        if (on_error) {
                            on_error(result, error);
                        }
                        self.render();
                    }
                    else {
                        setTimeout(_.bind(self.wait_for_room_state, self, !self.connected, 20), 3000);

                        if(on_success) {
                            on_success(result, error);
                        }
                        new AlertPopup($T("Success"), format(success_msg, {
                            room_name: self.booking.linkVideoRoomLocation,
                            booking_type: self.booking.type
                        })).open();
                    }
                } else {
                    IndicoUtil.errorReport(error);
                }
            });
    },

    disconnect_room: function(on_answer, on_success, on_error) {
        this.request_room("vidyo.disconnectVidyoBooking",
                          $T("The disconnection of the room {room_name} to the {booking_type} " +
                             "room has been requested. Please verify that the deviced has been disconnected."),
                          on_answer, on_success, on_error);
    },

    connect_room: function(on_answer, on_success, on_error) {
        var self = this;

        var request_connect = function(answer, force) {
            if (answer) {
                self.request_room("vidyo.connectVidyoBooking",
                                  $T("The connection of the room {room_name} to the {booking_type} " +
                                     "room has been requested. Please check that the device is already " +
                                     "connected and also do not forget to disconnect the room when the " +
                                     "meeting ends."),
                                  on_answer, on_success, on_error, {force: force});
            } else {
                self.render();
            }};

        var confirm_replace = function(msg) {
            new ConfirmPopup($T('Room already connected'),
                             msg,
                             function(answer) {
                                 request_connect(answer, true);
                             }).open();
        }

        if (this.connection.isConnected) {
            if (this.connection.service.toLowerCase() != this.booking.type.toLowerCase()) {
                confirm_replace(format($T('This room is currently connected to a {0} booking. Do you want to disconnect it?'),
                                       [this.connection.service]));
            } else if (this.booking.bookingParams.roomName != this.connection.roomName) {
                confirm_replace(format($T("This room is currently connected to another {0} room: '{1}'. Do you want to disconnect it?"),
                                        [this.connection.service, this.connection.roomName]));
            }
        } else {
            request_connect(true);
        }
    },

    wait_for_room_state: function(state, retries_left) {
        var self = this;
        this.check_room_connection(function(result) {
            if (result.isConnected == state || retries_left == 1) {
                self.render();
            } else {
                setTimeout(_.bind(self.wait_for_room_state, self, state, retries_left - 1), 3000);
            }
        });
    }
}, function(elem, booking, conf_id) {
    this.initialize(elem, booking, conf_id);
});


type("ManagementConnectButton", ["ConnectButton"], {
    connect_room: function() {
        var self = this;
        if (!pluginHasFunction(this.booking.type, "checkConnect") || codes[this.booking.type].checkConnect(this.booking)) {
            _.bind(this.ConnectButton.prototype.connect_room, this)(
                function() {
                }, function(result) {
                    connectBookingLocal(result);
                }, function(result, error) {
                    codes[self.booking.type].errorHandler('connect', result, self.booking);
                });
        }
    },

   disconnect_room: function() {
        var self = this;
        if (!pluginHasFunction(this.booking.type, "checkDisconnect") || codes[this.booking.type].checkDisconnect(this.booking)) {
            _.bind(this.ConnectButton.prototype.disconnect_room, this)(
                function() {
                }, function(result) {
                    disconnectBookingLocal(result);
                }, function(result, error) {
                    codes[self.booking.type].errorHandler('disconnect', result, booking);
                });
        }
    }

}, function(elem, booking, conf_id) {
    this.ConnectButton(elem, booking, conf_id);
    this.tpl = TPL_MANAGEMENT_BUTTON;
});


$(function() {
    $('.collaborationDisplayMoreInfo').click(function() {
        var newText = ($(this).text() == $T("More Info")) ? $T("Hide info") : $T("More Info");
        var textNode = $(this);
        $(this).closest('.videoServiceWrapper').next('.collabInfoInline').slideToggle('fast', function() {
            textNode.text(newText);
        });
    });

    $('.connect_room').each(function() {
        var conf_id = $(this).data('event');
        var booking = bookings[$(this).data('booking-id')];
        var button = new ConnectButton($(this), booking, conf_id);
    });

});
