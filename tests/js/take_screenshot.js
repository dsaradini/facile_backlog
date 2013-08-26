var USERNAME = "test@test.ch";
var PASSWORD = "test";

var LOGIN_URL = "/login";
var HOME_URL = "/home";

var END_ON_TIMEOUT = false;

var page = require('webpage').create(),
    system = require('system'),
    address, output, size;

address = system.args[1];
output = system.args[2];


var fn_steps = function(steps, end) {
	var index = 0;
	var _run = function() {
		if (index < steps.length && typeof steps[index] == 'function') {
			var curr_fun = steps[index];
			curr_fun(function(err) {
				if (err) {
					end(err);
				} else {
					index ++;
					_run()
				}
			})
		} else {
			end(null);
		}
	};
	_run();
};


page.viewportSize = { width: 1024, height: 600 };

var loadInProgress = false;

page.onConsoleMessage = function(msg) {
  console.log(msg);
};

page.onError = function(message, stack) {
	console.error("error: ("+page.frameUrl+")" + message, stack);
	stack.forEach(function(item) {
        console.log('  ', item.file, ':', item.line);
    })
};

page.onLoadStarted = function() {
  loadInProgress = true;
};

page.onLoadFinished = function() {
  loadInProgress = false;
};

var is_logged_in = false;
var login = function(url, end) {
	var interval = null;

	var timeout = setTimeout(function() {
		end(new Error("Timeout on address '"+url+"'"));
	}, 2000);

	var fn_end = function(err) {
		clearTimeout(timeout);
		clearInterval(interval);
		end(err)
	};

	var steps = [
		function() {
			//Load Login Page
			page.open(url,function(status) {
				if (status !== 'success') {
					end(new Error("Unable to log load address '"+url+"'"));
				}
			});
		},
		function() {
			//Enter Credentials
			page.evaluate(function() {
				var arr = document.querySelectorAll("#login_form");
				var i;
				for (i=0; i < arr.length; i++) {
					if (arr[i].getAttribute('method') == "POST") {
						arr[i].elements["id_username"].value="test@test.ch";
						arr[i].elements["id_password"].value="test";
						break;
					}
				}
			});
		},
		function() {
			//Login
			page.evaluate(function() {
				var arr = document.querySelectorAll("#login_form");
				var i;

				for (i=0; i < arr.length; i++) {
					if (arr[i].getAttribute('method') == "POST") {
						arr[i].submit();
						break;
					}
				}
			});
		},
		function() {
			// Output content of page to stdout after form has been submitted
			is_logged_in = true;
		}
	];

	var testindex = 0;
	interval = setInterval(function() {
		try {
			if (!loadInProgress && typeof steps[testindex] == "function") {
				steps[testindex]();
				testindex++;
			}
			if (typeof steps[testindex] != "function") {
				fn_end()
			}
		} catch (ex) {
			fn_end(ex)
		}
	}, 50);
};

var TITLES = {};
var nav_urls = {};

var get_unique_title = function(url) {
	var base_title = (is_logged_in?"login_":"anonymous_") + "_" + url.replace(/\W/g, "_");
	var title = base_title;
	var i = 1;
	while( TITLES[title] ) {
		title = base_title + "_" + i;
		i++;
	}
	TITLES[title] = true;
	return title;
};

var navigate = function(url, end) {
	var timeout = setTimeout(function() {
		var txt = "Timeout on address '"+url+"'";
		if (END_ON_TIMEOUT) {
			end(new Error(txt));
		} else {
			console.error(txt);
			end();
		}

	}, 10000);

	var fn_end = function(err) {
		end(err)
	};

	page.open(url, function (status) {
		clearTimeout(timeout);
		if (status !== 'success') {
			fn_end(new Error("Unable to load the address!"))
		} else {
			window.setTimeout(function () {
				var title = get_unique_title(url);
				var file_path = output+"/"+title+".png";
				try {
					var body = document.querySelectorAll("body");
					body[0].style.backgroundColor = "#000000";
					page.render(file_path);
					var links = page.evaluate(function() {
						var result = [];
						var links = document.getElementsByTagName("a");
						var i;
						for (i=0; i < links.length; i++) {
							var href = links[i].href;
							if (href) {
								result.push(href);
							}
						}
						return result;
					});
					var fn_follows = [];
					var i;
					for ( i=0; i < links.length; i++) {
						var fn = (function(link){
							return function(done) {
								follow_link(link, done);
							};
						})(links[i]);
						fn_follows.push(fn)
					}
					fn_steps(fn_follows, fn_end);
				} catch(e) {
					e.url = url;
					fn_end(e);
				}
			}, 200);
		}
	});
};

var ALREADY = {};
var follow_link = function(url, done) {
	url = url.replace("#", "");
	if (url.indexOf(address) == 0) {
		var key = (is_logged_in?"login_":"anonymous_") + url;
		if ( ALREADY[key]) {
			done();
		} else {
			ALREADY[key] = true;
			navigate(url, done);
		}
	} else {
		done();
	}
};

fn_steps([
	function(done) {
		navigate(address+HOME_URL, done);
	},
	function(done) {
		login(address+LOGIN_URL, done);
	},
	function(done) {
		navigate(address+HOME_URL, done);
	}
], function(err) {
	if (err) {
		console.error(err);
		phantom.exit(-1);
	} else {
		phantom.exit();
	}
});