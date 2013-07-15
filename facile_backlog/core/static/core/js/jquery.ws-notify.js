 (function ($) {
 	if(typeof $.ws_sbscribe == "undefined"){
		$.ws_sbscribe = function( options ) {
			var empty_fn = function() {};
			var reconnect_timeout = options.timeout || 5000;
			var message_callback = options.on_message;
			var disconnect_callback = options.on_disconnect || empty_fn;
			var connect_callback = options.on_connect || empty_fn;
			var error_callback = options.on_error || empty_fn;

			var ws_url = options.url;
			if (!("WebSocket" in window)) {
				// WebSocket not supported
				throw "WebSocket not supported in this browser";
			}
			var ws;
			var connect_ws = function() {
				ws = new WebSocket(ws_url);
				ws.onopen = function(){
					connect_callback();
				};
				ws.onmessage = function(ev){
					var data = JSON.parse(ev.data);
					message_callback(data);
				};
				ws.onclose = function(ev){
					disconnect_callback();
					setTimeout(connect_ws, reconnect_timeout);
				};
				ws.onerror = function(ev){
					error_callback();
				};
			};
			window.onbeforeunload = function() {
				ws.onclose = function () {}; // disable onclose handler first
				ws.close()
			};
			connect_ws();
		}
	}
 }(jQuery));