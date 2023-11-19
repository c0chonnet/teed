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

  for (let i = 1; i <= 28; i++) {
  const currentId = i.toString();
  const element = document.getElementById(currentId);

  if (element) {
    element.addEventListener("targetFound", event => {
      console.log(`${currentId} target found`);
      const target = { id: currentId };
      interactions.push(target);
      parent.document.getElementById('jsondata').value = JSON.stringify(interactions);
    });
  }
}

 });