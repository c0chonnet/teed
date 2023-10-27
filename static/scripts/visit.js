 document.addEventListener("DOMContentLoaded", function() {

	const sceneEl = document.querySelector('a-scene');
	let arSystem;
	sceneEl.addEventListener('loaded', function () {
	  arSystem = sceneEl.systems["mindar-image-system"];
	});

	var interactions=[]
	var currentDate = new Date();
	var startDate = currentDate.getDate().toString().padStart(2, '0') + '.' +
                (currentDate.getMonth() + 1).toString().padStart(2, '0') + '.' +
                currentDate.getFullYear() + ' ' +
                currentDate.getHours().toString().padStart(2, '0') + ':' +
                currentDate.getMinutes().toString().padStart(2, '0') + ':' +
                currentDate.getSeconds().toString().padStart(2, '0');
	parent.document.getElementById('start').value = startDate

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