/* background stars animation */

let hero = document.querySelector(".hero");

for(let i=0;i<70;i++){
let star = document.createElement("span");

star.style.position="absolute";
star.style.width="2px";
star.style.height="2px";
star.style.background="white";
star.style.top=Math.random()*100+"%";
star.style.left=Math.random()*100+"%";
star.style.opacity=Math.random();

hero.appendChild(star);
}
function openModel(){
    window.location.href = "model.html";
}
