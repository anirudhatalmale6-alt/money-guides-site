var CFG={"newsletter": "", "contact": ""};
function toggleMenu(b){var n=document.getElementById('nav');var o=n.classList.toggle('open');b.setAttribute('aria-expanded',o)}

var IDX=null;
function openSearch(){
  document.getElementById('search').hidden=false;
  var q=document.getElementById('q');q.value='';q.focus();
  document.getElementById('results').innerHTML='';
  if(!IDX) fetch(ROOT+'search.json').then(function(r){return r.json()}).then(function(d){IDX=d});
}
function closeSearch(){document.getElementById('search').hidden=true}
function runSearch(v){
  var ul=document.getElementById('results');ul.innerHTML='';
  v=v.trim().toLowerCase(); if(!v||!IDX) return;
  var words=v.split(/\s+/);
  var hits=IDX.filter(function(a){var t=(a.t+' '+a.e+' '+a.c).toLowerCase();return words.every(function(w){return t.indexOf(w)>-1})});
  if(!hits.length){ul.innerHTML='<li><span style="display:block;padding:12px 6px">No articles found.</span></li>';return}
  hits.forEach(function(a){
    var li=document.createElement('li'),link=document.createElement('a'),b=document.createElement('b'),s=document.createElement('span');
    link.href=ROOT+a.u;b.textContent=a.t;s.textContent=a.c;link.appendChild(b);link.appendChild(s);li.appendChild(link);ul.appendChild(li);
  });
}
document.addEventListener('keydown',function(e){if(e.key==='Escape')closeSearch()});
document.addEventListener('click',function(e){if(e.target.id==='search')closeSearch()});

// Newsletter: only says "subscribed" once a real email service has accepted it.
function post(f,url,okText,offText){
  var msg=f.querySelector('.news-msg');
  if(!url){msg.textContent=offText;return false}
  var btn=f.querySelector('button');btn.disabled=true;
  fetch(url,{method:'POST',body:new FormData(f)})
    .then(function(r){if(!r.ok)throw 0;msg.textContent=okText;f.reset()})
    .catch(function(){msg.textContent='Sorry, that did not go through. Please try again.'})
    .finally(function(){btn.disabled=false});
  return false;
}
function subscribe(f){return post(f,CFG.newsletter,'Thanks! Check your inbox to confirm.','Newsletter sign-up is not connected yet.')}
function contactForm(f){return post(f,CFG.contact,'Thanks, your message has been sent.','The contact form is not connected yet.')}
function shareIt(){
  var u=location.href;
  if(navigator.share){navigator.share({title:document.title,url:u}).catch(function(){})}
  else if(navigator.clipboard){navigator.clipboard.writeText(u).then(function(){alert('Link copied')})}
  return false;
}
var tt=document.querySelector('.to-top');
window.addEventListener('scroll',function(){tt.classList.toggle('show',scrollY>600)},{passive:true});
