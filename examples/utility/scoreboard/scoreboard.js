var CESIUM_ACCESS_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJlMGE4YTEyMi0wNzllLTRjYmItYTY3Ny1kOTA3YzEwNzk3ZDEiLCJpZCI6MTYyNzcsInNjb3BlcyI6WyJhc3IiLCJnYyJdLCJpYXQiOjE1NzAwNjA5MzF9.NgsS6QgAqCD3SkBP23vtQro_QWUDVgUnEEOW-UQ2ypQ';
			var BROKER_HOST = 'testbed.mysmce.com';
			var BROKER_PORT = 8443;
			var BROKER_CLIENT_USERNAME = 'mlevine4';
			var BROKER_CLIENT_PASSWORD = 'w6A1lKFiLT0K';
	  
			$(document).ready(function(){
				Cesium.Ion.defaultAccessToken = CESIUM_ACCESS_TOKEN;
				var clock = new Cesium.Clock({
						currentTime: Cesium.JulianDate.fromIso8601("1900-01-01"),
						clockStep: Cesium.ClockStep.SYSTEM_CLOCK_MULTIPLIER,
						multiplier: 0, // how much time to advance each SYSTEM CLOCK tick
						shouldAnimate: false,
					});
				const viewer = new Cesium.Viewer('cesiumContainer', {
					terrainProvider: Cesium.createWorldTerrain(),
					baseLayerPicker: false,
					homeButton: false,
					infoBox: false,
					geocoder: false,
					selectionIndicator: false,
					navigationHelpButton: false,
					navigationInstructionsInitiallyVisible: false,
					timeline: true,
					imageryProvider: new Cesium.IonImageryProvider({ assetId: 3845 }),
					clockViewModel: new Cesium.ClockViewModel(clock)
				});
				// <!-- viewer.scene.globe.enableLighting = true; -->

				// create a MQTT client
				var client = new Paho.MQTT.Client(BROKER_HOST, BROKER_PORT, "");
				var satellitesCapella = {}; //<!-- Positions of satellites as points at altitude, BLUE out of comms range, GREEN in comms range -->
				var satellitesPlanet = {}; //<!-- Positions of satellites as points at altitude, BLUE out of comms range, GREEN in comms range -->
				var sensorCirclesCapella = {}; //<!-- Circles showing views of nadir pointed satellites -->
				var sensorCirclesPlanet = {}; //<!-- Circles showing views of nadir pointed satellites -->
				var commsCones = {}; //<!-- Views from ground station FOR comms -->
				var commsRange = false; //<!-- Initialize this commsRange boolean as false, but will update based on satellite subscription -->
				var satColor = Cesium.Color.BLUE; //<!-- Initialize satColor as Cesium's default BLUE, which is color when commsRange is false -->
				var events = viewer.scene.primitives.add(new Cesium.PointPrimitiveCollection()); //<!-- Initialize events as primitive points since there will be so many -->
				var eventsById = {};
				var alphasById = {};
				var grounds = {}; //<!-- Surface position of ground stations as PINK points -->
				var updates = {};
				var eventIndex = 0;
				var nightAlpha = 0.25;

				function handleMessage(message) {
					// get the message payload as a string
					//<!-- console.log(message.payloadString); -->
					var payload = message.payloadString;
					var topic = message.destinationName;
					// try to parse and stringify a JSON string
					try {
						if(topic=="utility/manager/init") {
							payload = JSON.parse(message.payloadString);
							viewer.clockViewModel.currentTime = Cesium.JulianDate.fromIso8601(payload.taskingParameters.simStartTime);
							viewer.clockViewModel.startTime = Cesium.JulianDate.fromIso8601(payload.taskingParameters.simStartTime);
							viewer.clockViewModel.stopTime = Cesium.JulianDate.fromIso8601(payload.taskingParameters.simStopTime);
							viewer.clockViewModel.clockRange = Cesium.ClockRange.CLAMPED;
							viewer.timeline.zoomTo(viewer.clockViewModel.startTime,viewer.clockViewModel.stopTime);
						} else if(topic=="utility/manager/start") {
							payload = JSON.parse(message.payloadString);
							viewer.clockViewModel.multiplier = payload.taskingParameters.timeScalingFactor;
						} else if(topic=="utility/manager/time" || topic=="utility/manager/status/time") {
							payload = JSON.parse(message.payloadString);
							viewer.clockViewModel.currentTime = Cesium.JulianDate.fromIso8601(payload.properties.simTime);
							viewer.timeline.updateFromClock();
						} else if(topic=="utility/manager/update"){
							payload = JSON.parse(message.payloadString);
							viewer.clockViewModel.multiplier = payload.taskingParameters.timeScalingFactor;
						} else if(topic=="utility/capella/location") {
							payload = JSON.parse(message.payloadString);
							commRange = payload.commRange;
							if (commRange){
								satColor = Cesium.Color.GREEN
							} else {
								satColor = Cesium.Color.BLUE
							};
							if(satellitesCapella[payload.id]) {
								satellitesCapella[payload.id].position=Cesium.Cartesian3.fromDegrees(
									payload.longitude,
									payload.latitude,
									payload.altitude
								);
								satellitesCapella[payload.id].point.color = satColor;
								sensorCirclesCapella[payload.id].ellipse.semiMajorAxis = payload.radius;
								sensorCirclesCapella[payload.id].ellipse.semiMinorAxis = payload.radius;
								sensorCirclesCapella[payload.id].position=Cesium.Cartesian3.fromDegrees(
									payload.longitude,
									payload.latitude
								);
							} else {
								satellitesCapella[payload.id] = viewer.entities.add({
									position: Cesium.Cartesian3.fromDegrees(
										payload.longitude,
										payload.latitude,
										payload.altitude
									),
									point: {
										pixelSize: 8,
										color: satColor
									},
									label: {
										text: payload.name,
										font: "12px Georgia",
										fillColor: Cesium.Color.SKYBLUE,
										outlineColor: Cesium.Color.BLACK,
										outlineWidth: 2,
										style: Cesium.LabelStyle.FILL_AND_OUTLINE,
										pixelOffset: new Cesium.Cartesian2(40.0, 8.0),
										pixelOffsetScaleByDistance: new Cesium.NearFarScalar(
											1.5e2,
											3.0,
											1.5e7,
											0.5
										),
										scaleByDistance: new Cesium.NearFarScalar(1.5e2, 2.0, 1.5e7, 0.5),
										translucencyByDistance: new Cesium.NearFarScalar(
											1.5e2,
											1.0,
											1.5e8,
											0.0
										),
									},
									show: true
								});
								sensorCirclesCapella[payload.id]=viewer.entities.add({
									position: Cesium.Cartesian3.fromDegrees(
										payload.longitude,
										payload.latitude
									),
									ellipse: {
										semiMajorAxis: payload.radius,
										semiMinorAxis: payload.radius,
										material: Cesium.Color.BLUE.withAlpha(0.2)
									}
								});
							}
						} else if(topic=="utility/planet/location") {
							payload = JSON.parse(message.payloadString);
							commRange = payload.commRange;
							if (commRange){
								satColor = Cesium.Color.CHARTREUSE
							} else {
								satColor = Cesium.Color.AQUA
							};
							if(satellitesPlanet[payload.id]) {
								satellitesPlanet[payload.id].position=Cesium.Cartesian3.fromDegrees(
									payload.longitude,
									payload.latitude,
									payload.altitude
								);
								satellitesPlanet[payload.id].point.color = satColor;
								sensorCirclesPlanet[payload.id].ellipse.semiMajorAxis = payload.radius;
								sensorCirclesPlanet[payload.id].ellipse.semiMinorAxis = payload.radius;
								sensorCirclesPlanet[payload.id].position=Cesium.Cartesian3.fromDegrees(
									payload.longitude,
									payload.latitude
								);
							} else {
								satellitesPlanet[payload.id] = viewer.entities.add({
									position: Cesium.Cartesian3.fromDegrees(
										payload.longitude,
										payload.latitude,
										payload.altitude
									),
									point: {
										pixelSize: 8,
										color: satColor
									},
									label: {
										text: payload.name,
										font: "12px Georgia",
										fillColor: Cesium.Color.SKYBLUE,
										outlineColor: Cesium.Color.BLACK,
										outlineWidth: 2,
										style: Cesium.LabelStyle.FILL_AND_OUTLINE,
										pixelOffset: new Cesium.Cartesian2(40.0, 8.0),
										pixelOffsetScaleByDistance: new Cesium.NearFarScalar(
											1.5e2,
											3.0,
											1.5e7,
											0.5
										),
										scaleByDistance: new Cesium.NearFarScalar(1.5e2, 2.0, 1.5e7, 0.5),
										translucencyByDistance: new Cesium.NearFarScalar(
											1.5e2,
											1.0,
											1.5e8,
											0.0
										),
									},
									show: true
								});
								sensorCirclesPlanet[payload.id]=viewer.entities.add({
									position: Cesium.Cartesian3.fromDegrees(
										payload.longitude,
										payload.latitude
									),
									ellipse: {
										semiMajorAxis: payload.radius,
										semiMinorAxis: payload.radius,
										material: Cesium.Color.AQUA.withAlpha(0.2)
									}
								});
							}
						} else if(topic=="utility/event/start") {
							//<!-- Cesium suggests using PointPrimitives when have large collection of points, applies to events -->
							try {
								payload = JSON.parse(message.payloadString);
								if (payload.isDay==1) {
									alphasById[payload.eventId] = 1;
								} else {
									alphasById[payload.eventId] = nightAlpha;
								}

								eventsById[payload.eventId] = events.add({
									id: eventIndex,
									position: new Cesium.Cartesian3.fromDegrees(
										payload.longitude,
										payload.latitude
									),
									pixelSize: 8,
									color: Cesium.Color.RED.withAlpha(alphasById[payload.eventId]),
									show: true});
								eventIndex = eventIndex + 1;
							} catch {
								console.log("Error: utility/event/start");
							}
						} else if(topic=="utility/event/dayChange") {
							try {
								payload = JSON.parse(message.payloadString);
								if (payload.isDay==1) {
									alphasById[payload.eventId] = 1;
								} else {
									alphasById[payload.eventId] = nightAlpha;
								}
							} catch {
								console.log("Error: First half utility/event/dayChange")
							} try {
								currColor = events.get(eventsById[payload.eventId].id).color;
								events.get(eventsById[payload.eventId].id).color = currColor.withAlpha(alphasById[payload.eventId]);
							} catch {
								console.log("Error: Second half utility/event/dayChange")
							}
			
						} else if(topic=="utility/event/finish") {
							try {
								payload = JSON.parse(message.payloadString);
								events.get(eventsById[payload.eventId].id).show = false;
							} catch {
								console.log("Error: utility/event/finish");
							}
							
						} else if(topic=="utility/ground/location"){
							try {
								payload = JSON.parse(message.payloadString);
								activeCheck = payload.operational;
								if (activeCheck){
									groundColor = Cesium.Color.PINK
									groundMaterial = Cesium.Color.PINK.withAlpha(0.1)
								} else {
									groundColor = Cesium.Color.LIGHTGRAY
									groundMaterial = Cesium.Color.LIGHTGRAY.withAlpha(0.1)
								};
								if (!grounds[payload.groundId]) {
									//<!-- Only add grounds with unique ids -->
									grounds[payload.groundId] = viewer.entities.add({
										position: Cesium.Cartesian3.fromDegrees(
											payload.longitude,
											payload.latitude
										),
										point: {
											pixelSize: 8,
											color: groundColor
										},
										show: true
									});
									//<!-- Currently hardcoded cylinder dimensions, although angle read from message -->
									commsCones[payload.groundId] = viewer.entities.add({
										position: Cesium.Cartesian3.fromDegrees(
											payload.longitude,
											payload.latitude,
											100000.0
										),
										cylinder: {
											length: 200000.0,
											topRadius: 200000.0*Math.tan((90-payload.elevAngle)*Math.PI/180),
											bottomRadius: 0.0,
											material: groundMaterial,
											outline: true,
											outlineWidth: 1.0,
										}
									});
								}
							} catch {
								console.log("Error: utility/ground/location");
							}

						}
					} catch {
						console.log("An error was caught somewhere");
					}
				}

				client.connect({
					"userName": BROKER_CLIENT_USERNAME,
					"password": BROKER_CLIENT_PASSWORD,
					"useSSL": true,
					"onSuccess": function() {
						client.subscribe("utility/#", {
							"onFailure": function() {
								alert("Error subscribing to topic.");
							},
							"onSuccess": function() {
								client.onMessageArrived = handleMessage;
							}
						});
					}
				});
			});