/**
 * Hermes
 * @author Tom
 */

//http://ccmcu40.in2p3.fr/conference_participant_video.jpeg?conference=eAgora.cern.ch%2f13%238&participant=3

var RoomStatus = new Enum("Disconnected", "Connecting", "Connected", "Disconnecting");

var Hermes = {
	controls: {
		buildQuickTimeUrl: function(mcu, conference, pin) {
			return "rtsp://#{mcu}/conf_h264_g711u_384000_#{pin}_#{conference}"
				.interpolate({
					mcu: mcu,
					conference: conference,
					pin: encodeURIComponent(pin)
				});
		},
		buildRealPlayerUrl: function(mcu, conference, pin) {
			return "http://#{mcu}/rtsp_rpm_conf_h263_g711u_384000_#{pin}_#{conference}.rpm"
				.interpolate({
					mcu: mcu,
					conference: conference,
					pin: encodeURIComponent(pin)
				});
		},
		streamingControl: function(mcu, name, pin) {
			if (true) { // TODO switching between QuickTime and RealPlayer
				return Control.object(Type.QuickTime, {
					qtsrc: Hermes.controls.buildQuickTimeUrl(mcu, name, pin),
					src: "http://#{mcu}/conference.mov".interpolate({mcu: mcu}),
					autoplay: "true",
					controller: "false",
					kioskmode: "true",
					showlogo: "false",
					qtsrcdontusebrowser: "true",
					scale: "aspect"
				}, 400, 300);
			} else {
				return Control.object(Type.RealPlayer, {
					src: Hermes.controls.buildRealPlayerUrl(mcu, name, pin),
					autoplay: "true",
					controls: "imagewindow",
					console: "video"
				}, 400, 300);
			}
		}
	},
	ui: {
		createConference: function(fieldObj, submitAction, actionBox) {
			with (Html) with (Control) with (Field) {
				return box(
					h(4, $T("Hermes_Conference_New")),
					Table.create([
						labelled($T("Hermes_Conference_Title"),
							edit(), fieldObj, "title"
						),
						labelled($T("Hermes_Conference_StartDate"),
							dateEdit(fieldObj, "start")
						).addAll(
							labelled($T("Hermes_Conference_StartTime"),
								timeEdit(fieldObj, "start")
							)
						),
						labelled($T("Hermes_Conference_EndDate"),
							dateEdit(fieldObj, "end")
						).addAll(
							labelled($T("Hermes_Conference_EndTime"),
								timeEdit(fieldObj, "end")
							)
						)
					]),
					box(
						button($T("Hermes_Conference_Sumbit"), submitAction)
					),
					actionBox
				);
			}
		},
		showConference: function(properties, participantsSource, callButton) {
			with (Html) with (Control) with (Field) {
				return box(
					box(
						Hermes.controls.streamingControl(properties.get("mcu"), properties.get("name"), properties.get("pin"))
					).setStyle({"float": "right", marginBottom: "20px"}),
					h(4, $T("Hermes_Conference_Details")),
					table([
						labelled($T("Hermes_Conference_Title"), span(), properties, "title"),
						labelled($T("Hermes_Conference_Start"), span(), properties, "start"),
						labelled($T("Hermes_Conference_End"), span(), properties, "end")
					]),
					h(4, $T("Hermes_Conference_Login")),
					table([
						labelled($T("Hermes_Conference_Name"), span(), properties, "name"),
						labelled($T("Hermes_Conference_Id"), span(), properties, "id"),
						labelled($T("Hermes_Conference_Pin"), span(), properties, "pin")
					]),
					h(4, $T("Hermes_Participants")),
					remoteTable(participantsSource, [
							$T("Hermes_Participant_Name"),
							$T("Hermes_Participant_Address")
						], function(participant) {
							return [
								participant["name"],
								participant["address"]
							];
						}, {
							None: function(context) {
								context.set(loadingIcon());
							},
							Loading: function(context) {
								// nothing
							},
							Loaded: function(context, source) {
								var roomConnected = false;
								var roomAddress = properties.get("roomAddress");
								var participants = source.get(RemoteSource.Data);
								if (participants.length == 0) {
									context.set($T("Hermes_Participants_No"));
								} else {
									context.set("");
									roomConnected = $A(participants).any(function(participant) {
										if (participant.address == roomAddress) {
											properties.set("roomId", participant.id);
											return true;				
										}
									})
								}
								if (roomConnected) {
									if (properties.get("roomStatus") != RoomStatus.Disconnecting) {
										properties.set("roomStatus", RoomStatus.Connected);
									}
								} else {
									if (properties.get("roomStatus") != RoomStatus.Connecting) {
										properties.set("roomStatus", RoomStatus.Disconnected);
									}
								}
								participantsSource.update.bind(participantsSource).delay(5);
							},
							Error: function(context, source) {
								context.set("Error: " + source.get(RemoteState.Error));
								participantsSource.update.bind(participantsSource).delay(5);
							}
						}
					),
					Binding.objectToElement(box(), properties, "roomAddress", choice({
						"true": [
							h(4, $T("Hermes_Conference_Room")),
							table([
								labelled($T("Hermes_Conference_Room_Name"), span(), properties, "roomName"),
								labelled($T("Hermes_Conference_Room_Address"), span(), properties, "roomAddress")
							]),
							callButton
						]
					}, exists))
				);
			}
		},
		errorBox: function(message, details, retryAction) {
			with (Html) with (Control) {
				return box(
					h(4, $T("Hermes_Error")),
					box(message),
					box(details),
					button($T("Hermes_Error_Retry"), retryAction)
				);
			}
		}
	},
	action: {
		createConference: function() {
			var fieldObj = $O({
				conference: request.conference.id,
				title: request.conference.title,
				start: request.conference.start,
				end: request.conference.end
			});
			
			var actionBox = Control.box();
			
			var submit = function() {
				jsonRpc("hermes.conference.create", fieldObj,
					function(result, error) {
						if (exists(error)) {
							request.error = {
								message: $T("Hermes_Conference_CannotCreate"),
								details: error,
								retryAction: Hermes.action.createConference
							};
							Hermes.action.errorBox();
						} else {
							request.hermes = {
								conference: request.conference.id,
								id: result.id
							};
							Hermes.action.showConference();
						}
					}, Indico.Urls.JsonRpcService
				);
				actionBox.addContent(
					loadingIcon()
				);
			};
			
			$("hermesBody").update(Hermes.ui.createConference(fieldObj, submit, actionBox));
		},
		showConference: function() {
			$("hermesBody").update(
				Control.box(
					$T("Hermes_Conference_Loading"), " ", loadingIcon()
				)
			);
			var properties = $O({
				roomStatus: RoomStatus.Disconnected
			});
			properties.set("roomStatus", RoomStatus.Disconnected);
			var participants = new JsonRpcSource("hermes.conference.participant.list", {
					conference: request.conference.id,
					id: request.hermes.id
				}, Indico.Urls.JsonRpcService
			);
			
			var connect = function() {
				jsonRpc("hermes.conference.participant.connect", {
						conference: request.conference.id,
						id: request.hermes.id,
						address: properties.get("roomAddress")
					}, function(result, error) {
					}, Indico.Urls.JsonRpcService
				);
				properties.set("roomStatus", RoomStatus.Connecting);
				(function() {
					if (properties.get("roomStatus") == RoomStatus.Connecting) {
						properties.set("roomStatus", RoomStatus.Disconnected);
					}
				}).delay(20);
			};
			var disconnect = function() {
				jsonRpc("hermes.conference.participant.disconnect", {
						conference: request.conference.id,
						id: request.hermes.id,
						participant: properties.get("roomId")
					}, function(result, error) {
						error = error;
					}, Indico.Urls.JsonRpcService
				);
				properties.set("roomStatus", RoomStatus.Disconnecting);
				(function() {
					if (properties.get("roomStatus") == RoomStatus.Disconnecting) {
						properties.set("roomStatus", RoomStatus.Connected);
					}
				}).delay(20);
			};
			
			var callButton = Control.button();
			Binding.commands(properties, "roomStatus", {
				Disconnecting: function() {
					callButton.setContent($T("Hermes_Conference_Room_Disconnecting"));
					callButton.disabled = true;
					disconnect.detach(callButton);
				},
				Disconnected: function() {
					callButton.setContent($T("Hermes_Conference_Room_Connect"));
					callButton.disabled = false;
					disconnect.detach(callButton);
					connect.attach(callButton);
				},
				Connecting: function() {
					callButton.setContent($T("Hermes_Conference_Room_Connecting"));
					callButton.disabled = true;
					connect.detach(callButton);
				},
				Connected: function() {
					callButton.setContent($T("Hermes_Conference_Room_Disconnect"));
					callButton.disabled = false;
					connect.detach(callButton);
					disconnect.attach(callButton);
				}
			});
			
			jsonRpc("hermes.conference.query", {
					conference: request.conference.id,
					id: request.hermes.id
				}, function(result, error) {
					if (exists(error)) {
						request.error = {
							message: $T("Hermes_Conference_CannotLoad"),
							details: error,
							retryAction: Hermes.action.showConference
						};
						Hermes.action.errorBox();
					} else {
						properties.update(result);
						$("hermesBody").update(Hermes.ui.showConference(properties,
							participants, callButton));
					}
				}, Indico.Urls.JsonRpcService
			);
		},
		errorBox: function() {
			$("hermesBody").update(Hermes.ui.errorBox(request.error.message,
				request.error.details, request.error.retryAction));
		}
	}
};

window.onload = function() {
	var action = request.hermes.action;
	if (exists(action)) {
		var method = Hermes.action[action];
		method();
	}
};

