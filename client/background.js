var DEBUG = false;
var sockId;
var IP = "127.0.0.1";
var PORT = 8888;
var serverUrlBase = "http://" + IP + ":" + PORT;
var xmlhttp ;
chrome.webNavigation.onBeforeNavigate.addListener(onBeforeNavigateListener);

function test(){
	trace("url : " + serverUrlBase + "?score=10&url=http://www.wellsfargo.com");
	xml_http_post(serverUrlBase,"score=10&url=http://www.wellsfargo.com",	function (){
		trace("in the callback");
		if (xmlhttp.readyState == 4) { // 4 => loaded complete
			if (xmlhttp.status == 200) { // HTTP status code  ( 200 => OK )
				trace("connected");
				trace("responseText : " + xmlhttp.responseText);
				var score = parseInt(xmlhttp.responseText);
				if(score > 3) {
					var warnMsg = "This page could be fishing web site\n" + "address : " + "test" + "\n" + "suspiciousity : " + score;
					alert(warnMsg);
					createCustomAlert(warnMsg);
				}
			} else {
				trace("statusText: " + xmlhttp.statusText + "\nHTTP status code: " + xmlhttp.status);
			}
		}
	});
}

function onBeforeNavigateListener(details) {
	if(details == null || details.url == null) return;
	var score = computeSuspiciousity(details.url);
	trace("Send some message here");

	var url = serverUrlBase ;
	var param = "score=" + score + "&" + "url=" + details.url;
	trace("url : " + url);
	trace("param : " + param);
	xml_http_post(url,param,function (){
		if (xmlhttp.readyState == 4) { // 4 => loaded complete
			if (xmlhttp.status == 200) { // HTTP status code  ( 200 => OK )
				trace("connected");
				trace("responseText : " + xmlhttp.responseText);
				var score = parseInt(xmlhttp.responseText);
				if(score > 3) {
					var warnMsg = "This page MIGHT be a phishing site\n" ; /*"Address : " + details.url + "\n" + "suspiciousity : " + score;*/
					if(score > 6)
						warnMsg = "This page MAY be a phishing site\n";
					if(score > 9)
						warnMsg = "This page MUST be a phishing site\n";
					alert(warnMsg);
				}
			} else {
				trace("statusText: " + xmlhttp.statusText + "\nHTTP status code: " + xmlhttp.status);
			}
		}
	});
}

function xml_http_post(url,params, callback) {
	xmlhttp = new XMLHttpRequest();
	xmlhttp.open("POST", url, true);
	xmlhttp.onreadystatechange = callback;
	xmlhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
//	xmlhttp.setRequestHeader("Content-length", params.length);
//	xmlhttp.setRequestHeader("Connection", "close");
	xmlhttp.send(params);
	trace("after request");
}

function trace(str) {
	if(DEBUG == false) return;
	console.log(str);
}

function computeSuspiciousity(url){
	trace("");
	if(url == null) {
		trace("URL is null in computeSuspiciousity()")
		return;
	}
	var score = 0;
	var hostName = getHostName(url);
	if(hostName == null) return 0;
	trace("<" + hostName + ">");
	if (searchIPAddress(url) >= 0) {
		score++;
		trace("URL contains IP address.");
	}
	if (countDash(hostName) > 2 ) {
		score++;
		trace("Host name contains too many dashs.");
	}
	if (hostName.length > 22) {
		score++;
		trace("Host name is too long.");
	}
	if (countDot(url) > 3) {
		score++;
		trace("URL contains too many dots.");
	}
	if (countDot(hostName) > 2) {
		score++;
		trace("Host name contains too many dots.");
	}
	console.log("score : " + score);
	return score;
}
function searchIPAddress(url) {
	if (url == null) {
		console.error("URL is null in searchIPAdress()");
		return;
	}
	var patternIP = /(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)/;
	return url.search(patternIP);
}
function getHostName(url) {
	if (url == null) {
		console.error("URL is null in getHostName()");
		return;
	}
	var urlArr = url.split("://");
	if(urlArr == null || urlArr.length < 2) {
		trace("<problmatic url : " + url + ">");
		console.error("cannot parse the URL properly");
		return null;
	}
	var hostName = urlArr[1].split("/")[0];
	if(hostName == null) {
		trace("address : " + urlArr[1]);
		console.error("cannot parse the address properly");
		return null;
	}
	return hostName;	
}
function countDash(str) {
	if(str == null) {
		console.error("str is null in countDash()");
		return 0;
	}
	return str.split("-").length - 1;
}
function countDot(str) {
	if(str == null) {
		console.error("str is null in countDot()");
		return 0;
	}
	return str.split(".").length - 1;
}
