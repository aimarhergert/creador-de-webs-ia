document.addEventListener('DOMContentLoaded',()=>{

const navbar=document.getElementById('navbar');
const mobileMenuBtn=document.getElementById('mobile-menu-btn');
const mobileMenu=document.getElementById('mobile-menu');
const menuIconOpen=document.getElementById('menu-icon-open');
const menuIconClose=document.getElementById('menu-icon-close');

// 1. NAVBAR SCROLL
window.addEventListener('scroll',()=>{
  const scrolled=window.scrollY>10;
  navbar.classList.toggle('navbar-scrolled',scrolled);
  navbar.classList.toggle('bg-slate-950/90',scrolled);
  navbar.classList.toggle('backdrop-blur-xl',scrolled);
  navbar.classList.toggle('shadow-xl',scrolled);
  navbar.classList.toggle('shadow-black/20',scrolled);
},{passive:true});

// 2. MOBILE MENU
const toggleMenu=open=>{
  mobileMenu.classList.toggle('hidden',!open);
  menuIconOpen.classList.toggle('hidden',open);
  menuIconClose.classList.toggle('hidden',!open);
};
mobileMenuBtn?.addEventListener('click',e=>{
  e.stopPropagation();
  toggleMenu(mobileMenu.classList.contains('hidden'));
});
document.addEventListener('click',e=>{
  if(!mobileMenu?.classList.contains('hidden')&&!mobileMenu.contains(e.target)&&e.target!==mobileMenuBtn)toggleMenu(false);
});
mobileMenu?.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>toggleMenu(false)));

// 3. SCROLL ANIMATIONS
const animObserver=new IntersectionObserver(entries=>{
  entries.forEach(entry=>{
    if(entry.isIntersecting){
      const el=entry.target;
      const siblings=[...el.parentElement.children].filter(c=>c.hasAttribute('data-animate'));
      const idx=siblings.indexOf(el);
      el.style.transitionDelay=`${idx*80}ms`;
      el.classList.add('is-visible');
      animObserver.unobserve(el);
    }
  });
},{threshold:0.2});
document.querySelectorAll('[data-animate]').forEach(el=>animObserver.observe(el));

// 4. FAQ ACCORDION
document.querySelectorAll('.faq-item').forEach(item=>{
  const btn=item.querySelector('button');
  const answer=item.querySelector('.faq-answer');
  if(!btn||!answer)return;
  answer.style.overflow='hidden';
  answer.style.height='0';
  answer.style.transition='height 300ms ease';
  btn.addEventListener('click',()=>{
    const isOpen=answer.style.height!=='0px'&&answer.style.height!=='0';
    document.querySelectorAll('.faq-item').forEach(other=>{
      const oa=other.querySelector('.faq-answer');
      const ob=other.querySelector('button');
      if(oa&&oa!==answer){oa.style.height='0';ob?.querySelector('.faq-icon')&&(ob.querySelector('.faq-icon').textContent='+');}
    });
    answer.style.height=isOpen?'0':`${answer.scrollHeight}px`;
    const icon=btn.querySelector('.faq-icon');
    if(icon)icon.textContent=isOpen?'+':'×';
  });
});

// 5. STATS COUNTER
const easeOut=t=>1-Math.pow(1-t,3);
const animateCounter=el=>{
  const target=parseFloat(el.dataset.target)||0;
  const suffix=el.dataset.suffix||'';
  const duration=1500;
  const start=performance.now();
  const tick=now=>{
    const elapsed=now-start;
    const progress=Math.min(elapsed/duration,1);
    const value=target*easeOut(progress);
    el.textContent=(Number.isInteger(target)?Math.round(value):value.toFixed(1))+suffix;
    if(progress<1)requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
};
const statObserver=new IntersectionObserver(entries=>{
  entries.forEach(entry=>{
    if(entry.isIntersecting){animateCounter(entry.target);statObserver.unobserve(entry.target);}
  });
},{threshold:0.5});
document.querySelectorAll('.stat-number').forEach(el=>statObserver.observe(el));

// 6. SMOOTH SCROLL
document.querySelectorAll('a[href^="#"]').forEach(a=>{
  a.addEventListener('click',e=>{
    const target=document.querySelector(a.getAttribute('href'));
    if(!target)return;
    e.preventDefault();
    window.scrollTo({top:target.getBoundingClientRect().top+window.scrollY-80,behavior:'smooth'});
  });
});

// 7. CONTACT FORM
const contactForm=document.getElementById('contact-form');
const formSuccess=document.getElementById('form-success');
contactForm?.addEventListener('submit',e=>{
  e.preventDefault();
  const name=contactForm.querySelector('[name="name"]');
  const email=contactForm.querySelector('[name="email"]');
  const message=contactForm.querySelector('[name="message"]');
  if(!name?.value.trim()||!email?.value.trim()||!message?.value.trim())return;
  const btn=contactForm.querySelector('button[type="submit"]');
  const original=btn.textContent;
  btn.disabled=true;btn.textContent='Enviando...';
  setTimeout(()=>{
    contactForm.style.display='none';
    if(formSuccess){
      formSuccess.textContent='¡Mensaje enviado con éxito! Nos pondremos en contacto contigo en las próximas 24 horas. Gracias por escribirnos.';
      formSuccess.classList.remove('hidden');
      formSuccess.style.animation='slideIn 400ms ease forwards';
    }
    btn.disabled=false;btn.textContent=original;
  },1200);
});

// 8. NEWSLETTER FORM
const newsletterForm=document.getElementById('newsletter-form');
newsletterForm?.addEventListener('submit',e=>{
  e.preventDefault();
  const emailInput=newsletterForm.querySelector('[type="email"]');
  if(!emailInput?.value.trim())return;
  const btn=newsletterForm.querySelector('button[type="submit"]');
  const original=btn.textContent;
  btn.disabled=true;btn.textContent='Suscribiendo...';
  setTimeout(()=>{
    btn.disabled=false;btn.textContent=original;
    let msg=newsletterForm.querySelector('.newsletter-success');
    if(!msg){msg=document.createElement('p');msg.className='newsletter-success text-green-400 text-sm mt-2';newsletterForm.appendChild(msg);}
    msg.textContent='¡Suscripción confirmada! Recibirás nuestras novedades pronto.';
    emailInput.value='';
  },1200);
});

// 9. ACTIVE NAV LINK
const path=window.location.pathname.split('/').pop()||'index.html';
document.querySelectorAll('nav a').forEach(a=>{
  const href=a.getAttribute('href')?.split('/').pop()||'';
  if(href===path||(!href&&path==='index.html'))a.classList.add('text-white','font-semibold');
});

});