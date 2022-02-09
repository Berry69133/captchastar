import * as utils from './utils.js'

const advertiser_logout_url = "https://captchastart-advertiser.auth.eu-central-1.amazoncognito.com/logout?client_id=26edtp7ja5jv9gat8jkl7f4ic2&logout_uri=https://d30kz89fqvlj9d.cloudfront.net/index.html"
const publisher_logout_url = "https://captchastar-publisher.auth.eu-central-1.amazoncognito.com/logout?client_id=5jrffj0h8hfcfahg1l56c5um71&logout_uri=https://d30kz89fqvlj9d.cloudfront.net/index.html"

//authorization utilities

export function login(id_token, email){
	sessionStorage.setItem('id_token', id_token)
	sessionStorage.setItem('email', email)
}

//generic logout utility functions
function logout(logout_url){
	sessionStorage.clear()
	window.location.replace(logout_url)
}

function advertiser_logout(){
	logout(advertiser_logout_url)
}

function publisher_logout(){
	logout(publisher_logout_url)
}

export function isLogged(){
	return (sessionStorage.getItem('id_token') != null)
}

//initialization of auth features
window.onload = async () => {  
	// save id token if present
	const fragments = utils.getFragments() //get data from the URL

	if(fragments['id_token']){
		id_token = fragments['id_token']
		email = utils.getEmail(id_token)
        login(id_token, email)
    }

    //set the logout buttons
    //if there is no advertiser button (error is raised), check for the publisher one 
    try{ 
		document.getElementById('advertiser_logout_button').addEventListener('click', advertiser_logout)
    } catch(err){
	    document.getElementById('publisher_logout_button').addEventListener('click', publisher_logout)
    }
}





