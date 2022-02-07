//returns the information in the URL into a dict
export function getFragments(){
	let fragments_dict = {}
	if(window.location.hash){
		let hash = window.location.hash.substring(1)
		let fragments = hash.split('&')
		for(let i in fragments){
			let key_value = fragments[i].split('=')
			fragments_dict[key_value[0]] = key_value[1]
		}
	}
	return fragments_dict
}