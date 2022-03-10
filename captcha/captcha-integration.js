//constants
const POINT_SIZE=4;
const CAPTCHA_API = "https://9ozhfm2lxl.execute-api.eu-central-1.amazonaws.com/captchastar-get-ad";
const GET_AD_API = CAPTCHA_API + "/captcha"
const SOLUTION_API = CAPTCHA_API + "/solution"

//global variables 
let stars = []; 
let id_captcha = -1

//everything bootstraps here --------
restart();
//-----------------------------------

function Point(mxx, mxy, cx, myx, myy, cy){
	this.mxx = mxx;
	this.mxy = mxy;
	this.cx = cx;
	this.myx = myx;
	this.myy = myy;
	this.cy = cy;
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

	let mousePos = getMousePos(canvas, evt);
	let mousex=Math.round(mousePos.x);
	let mousey=Math.round(mousePos.y);

	let response = await checkSolution(mousex, mousey);
	let success = response['success'];
	let img_base64 = response['img_base64'];

	canvas.removeEventListener('mousemove', anima ,false);
	canvas.removeEventListener('click', controlla ,false);

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

async function load(){
	//reset canvas
	let hour = getHour();
	let site_id = "https://d2ehxhfky3kj2k.cloudfront.net" //TODO: remove, it should be inferred by the domain
	let res = await getCaptcha(site_id, hour);
	// store values relative to the capctha in the GLOBAL variables
	id_captcha = res['id_captcha'];
	lines = res['stars'].split("@"); 
	stars = parseLines(lines);
	//draw
	disegna(150,150);
}

async function getCaptcha(site_id, hour){
	let res = {};
	const get_capthca_url = GET_AD_API + "?site_id=" + site_id + "&hour=" + hour;
	const response = await fetch(get_capthca_url, {
    		method: 'GET',
    		headers: {
    			'Content-Type':'application/json'
    		}
	});

	const status = response.status;
	if(status != 200)
		throw new Error("Request Failed")

	let response_body = (await response.json())['body'];
	res['stars'] = response_body['stars'];
	res['id_captcha'] = response_body['id_captcha'];

	return res;
}

function restart(){
	let canvas = document.getElementById("captcha");
	let ctx = canvas.getContext("2d");
	ctx.fillStyle = "#FFFFFF";
	canvas.addEventListener('mousemove', anima, false);
	canvas.addEventListener('click', controlla, false);
	load();
}