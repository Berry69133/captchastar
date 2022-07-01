//constants
const POINT_SIZE=4;
const CAPTCHA_API = "https://9ozhfm2lxl.execute-api.eu-central-1.amazonaws.com/captchastar-get-ad";
const GET_AD_API = CAPTCHA_API + "/captcha"
const SOLUTION_API = CAPTCHA_API + "/solution"
const UPDATE_CLICK = CAPTCHA_API + "/click"

//global variables 
let stars = []; 
let id_captcha = -1
let auction_id = ''

//test
let t1 = 0;
let t2 = 0;

//global variables related to touch
let virtualMouseX = 0;
let virtualMouseY = 0;
let dragging = false;
let tapX, tapY, oldTapX, oldTapY;
let checkPerformed=false;

//everything bootstraps here--
let virtualMousePic = init();
restart();
//----------------------------

function init(){
	let checkmobile_button = document.getElementById("mobilecheck");
	let is_touch = isTouchSupported();
	let virtualMousePic = new Image();

	if(is_touch){
		checkmobile_button.style.display="inline";
		checkmobile_button.addEventListener("click", controlla)
		enableTouchListeners();
		virtualMousePic.src = "res/mouse.png";
		return virtualMousePic
	}
	else {
		checkmobile_button.style.display="none";
		enableMouseListeners();	
	}
}

function restart(){
	let canvas = document.getElementById("captcha");
	let ctx = canvas.getContext("2d");
	ctx.fillStyle = "#FFFFFF";
	
	let is_touch = isTouchSupported();
	if (is_touch){
		checkPerformed=false;
		virtualMousePic.src="res/mouse.png";
	}
	t1 = performance.now();
	load();
}

function Point(mxx, mxy, cx, myx, myy, cy){
	this.mxx = mxx;
	this.mxy = mxy;
	this.cx = cx;
	this.myx = myx;
	this.myy = myy;
	this.cy = cy;
}

function enableTouchListeners(){
	let canvas = document.getElementById("captcha");
	canvas.addEventListener("touchmove", touchMove);
	canvas.addEventListener("touchstart", touchClick);
	canvas.addEventListener("touchend", touchReleased);
}

//aka mossoTap
function touchMove(evt){
	evt.preventDefault();
    if(!dragging) return;
    if(checkPerformed) return;
    //dragging=true;
    oldTapX = tapX;
    oldTapY = tapY;
    tapX = evt.targetTouches[0].pageX;
    tapY = evt.targetTouches[0].pageY;
    let Xamount=Math.abs(oldTapX-tapX)/(window.innerWidth/300);
    let Yamount=Math.abs(oldTapY-tapY)/(window.innerHeight/300);

    if(oldTapX>tapX) virtualMouseX-=Xamount;
    else if(oldTapX<tapX) virtualMouseX+=Xamount;
    if(virtualMouseX<10) virtualMouseX=10;
    if(virtualMouseX>290) virtualMouseX=290;

    if(oldTapY>tapY) virtualMouseY-=Yamount;
    else if(oldTapY<tapY) virtualMouseY+=Yamount;
    if(virtualMouseY<10) virtualMouseY=10;
    if(virtualMouseY>290) virtualMouseY=290;

    disegna(virtualMouseX,virtualMouseY);
    let canvas = document.getElementById("captcha");
	let ctx = canvas.getContext("2d");
    ctx.drawImage(virtualMousePic,virtualMouseX,virtualMouseY);
}

//aka cliccatoTap
function touchClick(evt){
	//document.title="tapped";
    evt.preventDefault();
    dragging = true;
    tapX = evt.targetTouches[0].pageX;
    tapY = evt.targetTouches[0].pageY;
}

//aka rilasciatoTap
function touchReleased(evt){
	//document.title="released";
    evt.preventDefault();
    dragging=false;
}

function enableMouseListeners(){
	let canvas = document.getElementById("captcha");
	canvas.addEventListener('mousemove', anima, false);
	canvas.addEventListener('click', controlla, false);
}

function isTouchSupported() {
    let msTouchEnabled = window.navigator.msMaxTouchPoints;
    let generalTouchEnabled = "ontouchstart" in document.createElement("div");
    return (msTouchEnabled || generalTouchEnabled)
}

function showOriginalImage(img_base64){
	const img_src = "data:image/png;base64," + img_base64;
	let img = new Image();    
    let canvas = document.getElementById("captcha");
    let ctx = canvas.getContext("2d");

    img.onload = function() {
	  ctx.drawImage(this, 0, 0, canvas.width, canvas.height);
	}
    img.src = img_src;
    canvas.addEventListener('click', update_impression, false);
}

function update_impression(){
	let = url = UPDATE_CLICK + '?auction_id=' + auction_id
	fetch(url, {
    		method: 'PUT',
    		headers: {
    			'Content-Type':'application/json'
    		}
    	})
}

async function checkSolution(mysol_x, mysol_y){
	const get_sol_url = SOLUTION_API + "?mysol_x=" + mysol_x + "&mysol_y=" + mysol_y + "&id_captcha=" + id_captcha;
	const response = await fetch(get_sol_url, {
    		method: 'GET',
    		headers: {
    			'Content-Type':'application/json'
    		}
	});

	const status = response.status;
	if(status != 200)
		throw new Error("Request Failed");

	let response_body = (await response.json())['body'];
	return response_body;
}

async function controlla(evt){
	let canvas = document.getElementById("captcha");
	let rect = canvas.getBoundingClientRect();
	let is_touch = isTouchSupported();
	let mysol_x, mysol_y
	
	if (!is_touch){
		let mousePos = getMousePos(canvas, evt);
		mysol_x = Math.round(mousePos.x);
		mysol_y = Math.round(mousePos.y);
		canvas.removeEventListener('mousemove', anima ,false);
		canvas.removeEventListener('click', controlla ,false);
	} else {
		if(checkPerformed) 
			return;
		checkPerformed = true;
		mysol_x = Math.round(virtualMouseX);
		mysol_y = Math.round(virtualMouseY);
	}
	let response = await checkSolution(mysol_x, mysol_y);
	let success = response['success'];
	let img_base64 = response['img_base64'];

	if(success){
		showOriginalImage(img_base64);
	}else{
		restart();
	}
}

function anima(evt) {
	let canvas = document.getElementById("captcha");
	let ctx = canvas.getContext("2d");
	let mousePos = getMousePos(canvas, evt);
	let mousex = mousePos.x;
	let mousey = mousePos.y;	
	disegna(mousex,mousey);
}

function bug_workaround() {
	let canvas = document.getElementById("captcha");
	canvas.style.opacity = 0.99;
	setTimeout(function() {
		canvas.style.opacity = 1;
	}, 1);
}

function disegna(mousex,mousey) {
	let canvas = document.getElementById("captcha");
	let ctx = canvas.getContext("2d");
	// store the current transformation matrix
	ctx.save();
	// use the identity matrix while clearing the canvas
	ctx.setTransform(1, 0, 0, 1, 0, 0);
	ctx.clearRect(0, 0, canvas.width, canvas.height);
	// restore the transform
	ctx.restore();
	bug_workaround();

	//draw everything
	mousex = mousex/100000
	mousey = mousey/100000
	for(i=0;i<stars.length;i++){
		y=stars[i].myx*mousex+stars[i].myy*mousey+stars[i].cy-POINT_SIZE/2;
		x=stars[i].mxy*mousey+stars[i].mxx*mousex+stars[i].cx-POINT_SIZE/2;
		// if we pass the coordinates in the order (x,y), the image gets rotated by 90°
		ctx.fillRect(y,x,POINT_SIZE,POINT_SIZE);
	}
}

function getMousePos(canvas, evt) {
    let rect = canvas.getBoundingClientRect();
    let newX = evt.clientX - rect.left;
    let newY = evt.clientY - rect.top;
    return {
        x: newX,
        y: newY
    };
}

function parseLines(lines){
	let i=1;
	let res = []

	while(true){ 
		mxx=parseInt(lines[i]);
		if(isNaN(mxx)) break;
		lines[i]=lines[i].substring(lines[i].indexOf(" ")+1);		
		mxy=parseInt(lines[i]);
		lines[i]=lines[i].substring(lines[i].indexOf(" ")+1);		
		cx=parseInt(lines[i]);
		lines[i]=lines[i].substring(lines[i].indexOf(" ")+1);		
		myx=parseInt(lines[i]);
		lines[i]=lines[i].substring(lines[i].indexOf(" ")+1);		
		myy=parseInt(lines[i]);
		lines[i]=lines[i].substring(lines[i].indexOf(" ")+1);		
		cy=parseInt(lines[i]);
		//line = moltiplicatoreXX moltiplicatoreXY costanteX moltiplicatoreYX moltiplicatoreYY costanteY
		res.push(new Point(mxx, mxy, cx, myx, myy, cy));
		i++;
	}
	return res;
}

function getHour(){
	let today = new Date();
	let hour = today.getHours();
	return hour
}

function getDay(){
	let today = new Date();
	let weekday = today.getDay();
	return weekday
}

function getUserAgent() { 
	let browser = "None";
	let os = "None";
    if((navigator.userAgent.indexOf("Opera") || navigator.userAgent.indexOf('OPR')) != -1 ) {
        browser = 'Opera';
    } else if(navigator.userAgent.indexOf("Chrome") != -1 ) {
        browser = 'Chrome';
    } else if(navigator.userAgent.indexOf("Safari") != -1) {
        browser = 'Safari';
    } else if(navigator.userAgent.indexOf("Firefox") != -1 ){
        browser = 'Firefox';
    } else if((navigator.userAgent.indexOf("MSIE") != -1 ) || (!!document.documentMode == true )) {
        browser = 'Internet Explorer';
    } 
    if (navigator.appVersion.indexOf("Win") != -1) os = "Windows";
    if (navigator.appVersion.indexOf("Mac") != -1) os = "MacOS";
    if (navigator.appVersion.indexOf("X11") != -1) os = "UNIX";
    if (navigator.appVersion.indexOf("Linux") != -1) os = "Linux";

    useragent = {
    	"os": os,
    	"browser": browser
    }
    return useragent
}

async function getPosition(){
	const request = await fetch("https://ipinfo.io/json");
	const position = await request.json();
	return {
		"region": position.country,
		"city": position.city
	}
}

async function load(){
	// retrieve slot data
	let hour = getHour();
	let weekday = getDay();
	let useragent = getUserAgent();
	let os = useragent.os;
	let browser = useragent.browser;
	let position = await getPosition();
	let region = position.region;
	let city = position.city;
	//let site_id = window.location.hostname 
	let site_id = "https://d2ehxhfky3kj2k.cloudfront.net" 	

	let res = await getCaptcha(site_id, weekday, hour, os, browser, region, city);
	// store values relative to the capctha in the GLOBAL variables
	t2 = performance.now()
	console.log((t2 - t1)/1000)
	auction_id = res['auction_id'];
	id_captcha = res['id_captcha'];
	lines = res['stars'].split("@"); 
	stars = parseLines(lines);
	//draw
	disegna(150,150);
}

async function getCaptcha(site_id, weekday, hour, os, browser, region, city){
	let res = {};
	const get_capthca_url = GET_AD_API + "?site_id=" + site_id + "&hour=" + hour + "&weekday=" + weekday + "&os=" + os + "&browser=" + browser + "&region=" + region + "&city=" + city 
	const response = await fetch(get_capthca_url, {
    		method: 'GET',
    		headers: {
    			'Content-Type':'application/json',
    		}
	});

	const status = response.status;
	if(status != 200)
		throw new Error("Request Failed")

	let response_body = (await response.json())['body'];
	return response_body;
}