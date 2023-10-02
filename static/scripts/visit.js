 document.addEventListener("DOMContentLoaded", function() {

	const sceneEl = document.querySelector('a-scene');
	let arSystem;
	sceneEl.addEventListener('loaded', function () {
	  arSystem = sceneEl.systems["mindar-image-system"];
	});

	var interactions=[]

    document.getElementById('77').addEventListener("targetFound", event => {
	  console.log("77 target found");
	  target={}
	  target['id'] = 77;
	  interactions.push(target)
	   parent.document.getElementById('jsondata').value = JSON.stringify(interactions);
        });

document.getElementById('84').addEventListener("targetFound", event => {
	  console.log("84 target found");
	  target={}
	  target['id'] = 84;
	  interactions.push(target)
	   parent.document.getElementById('jsondata').value = JSON.stringify(interactions);
        });

document.getElementById('85').addEventListener("targetFound", event => {
	  console.log("85 target found");
	  target={}
	  target['id'] = 85;
	  interactions.push(target)
	   parent.document.getElementById('jsondata').value = JSON.stringify(interactions);
        });

document.getElementById('89').addEventListener("targetFound", event => {
	  console.log("89 target found");
	 target={}
	  target['id'] = 89;
	  interactions.push(target)
	   parent.document.getElementById('jsondata').value = JSON.stringify(interactions);
        });


 });