const navbar = document.getElementById('navbar');
const mobileMenuBtn = document.getElementById('mobile-menu-btn');
const mobileMenu = document.getElementById('mobile-menu');
const menuIconOpen = document.getElementById('menu-icon-open');
const menuIconClose = document.getElementById('menu-icon-close');

function handleNavbarScroll() {
  const scrolled = window.scrollY > 20;
  navbar.classList.toggle('navbar-scrolled', scrolled);
  navbar.classList.toggle('bg-slate-950/90', scrolled);
  navbar.classList.toggle('backdrop-blur-xl', scrolled);
  navbar.classList.toggle('shadow-xl', scrolled);
  navbar.classList.toggle('shadow-black/20', scrolled);
}

window.addEventListener('scroll', handleNavbarScroll, { passive: true });

function closeMobileMenu() {
  mobileMenu.classList.add('hidden');
  menuIconOpen.classList.remove('hidden');
  menuIconClose.classList.add('hidden');
}

if (mobileMenuBtn) {
  mobileMenuBtn.addEventListener('click', e => {
    e.stopPropagation();
    const isHidden = mobileMenu.classList.toggle('hidden');
    menuIconOpen.classList.toggle('hidden', !isHidden);
    menuIconClose.classList.toggle('hidden', isHidden);
  });
}

document.addEventListener('click', e => {
  if (mobileMenu && !mobileMenu.contains(e.target) && e.target !== mobileMenuBtn) {
    closeMobileMenu();
  }
});

mobileMenu && mobileMenu.querySelectorAll('a').forEach(a => a.addEventListener('click', closeMobileMenu));

const animObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const el = entry.target;
      const siblings = el.parentElement ? [...el.parentElement.querySelectorAll('[data-animate]')] : [];
      const idx = siblings.indexOf(el);
      if (idx > 0) el.style.transitionDelay = `${idx * 100}ms`;
      el.classList.add('is-visible');
      animObserver.unobserve(el);
    }
  });
}, { threshold: 0.2 });

document.querySelectorAll('[data-animate]').forEach(el => animObserver.observe(el));

document.querySelectorAll('.faq-item').forEach(item => {
  const btn = item.querySelector('button');
  const answer = item.querySelector('.faq-answer');
  const icon = btn && btn.querySelector('.faq-icon');
  if (!btn || !answer) return;
  answer.style.height = '0';
  answer.style.overflow = 'hidden';
  answer.style.transition = 'height 300ms ease';
  btn.addEventListener('click', () => {
    const isOpen = answer.dataset.open === 'true';
    document.querySelectorAll('.faq-answer[data-open="true"]').forEach(a => {
      a.style.height = '0';
      a.dataset.open = 'false';
      const ic = a.closest('.faq-item')?.querySelector('.faq-icon');
      if (ic) ic.textContent = '+';
    });
    if (!isOpen) {
      answer.style.height = answer.scrollHeight + 'px';
      answer.dataset.open = 'true';
      if (icon) icon.textContent = '×';
    }
  });
});

function animateCounter(el) {
  const target = parseFloat(el.dataset.target) || 0;
  const suffix = el.dataset.suffix || '';
  const duration = 1500;
  const start = performance.now();
  const isDecimal = target % 1 !== 0;
  function step(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    const value = target * ease;
    el.textContent = (isDecimal ? value.toFixed(1) : Math.floor(value)) + suffix;
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

const statObserver = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      animateCounter(entry.target);
      statObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.5 });

document.querySelectorAll('.stat-number[data-target]').forEach(el => statObserver.observe(el));

document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    const id = a.getAttribute('href').slice(1);
    const target = document.getElementById(id);
    if (!target) return;
    e.preventDefault();
    const top = target.getBoundingClientRect().top + window.scrollY - 80;
    window.scrollTo({ top, behavior: 'smooth' });
  });
});

const contactForm = document.getElementById('contact-form');
const formSuccess = document.getElementById('form-success');

if (contactForm) {
  contactForm.addEventListener('submit', e => {
    e.preventDefault();
    const name = contactForm.querySelector('[name="name"]');
    const email = contactForm.querySelector('[name="email"]');
    const message = contactForm.querySelector('[name="message"]');
    if (!name?.value.trim() || !email?.value.trim() || !message?.value.trim()) {
      [name, email, message].forEach(f => {
        if (f && !f.value.trim()) f.style.outline = '2px solid #ef4444';
      });
      return;
    }
    const btn = contactForm.querySelector('button[type="submit"]');
    const originalText = btn.textContent;
    btn.textContent = 'Enviando...';
    btn.disabled = true;
    setTimeout(() => {
      contactForm.style.display = 'none';
      if (formSuccess) {
        formSuccess.textContent = '¡Gracias! Tu mensaje ha sido recibido. Nuestro equipo se pondrá en contacto contigo en menos de 24 horas.';
        formSuccess.classList.remove('hidden');
        formSuccess.style.animation = 'slideIn 0.4s ease forwards';
      }
      btn.textContent = originalText;
      btn.disabled = false;
    }, 1200);
  });
}

const newsletterForm = document.getElementById('newsletter-form');

if (newsletterForm) {
  newsletterForm.addEventListener('submit', e => {
    e.preventDefault();
    const emailField = newsletterForm.querySelector('[name="email"], [type="email"]');
    if (!emailField?.value.trim() || !/\S+@\S+\.\S+/.test(emailField.value)) {
      if (emailField) emailField.style.outline = '2px solid #ef4444';
      return;
    }
    const btn = newsletterForm.querySelector('button[type="submit"]');
    const originalText = btn.textContent;
    btn.textContent = 'Suscribiendo...';
    btn.disabled = true;
    setTimeout(() => {
      newsletterForm.innerHTML = '<p style="color:#4ade80;font-weight:600;text-align:center">✓ ¡Suscripción confirmada! Pronto recibirás nuestras ofertas exclusivas.</p>';
    }, 1200);
  });
}

const path = window.location.pathname.replace(/\/$/, '') || '/';
document.querySelectorAll('nav a[href]').forEach(a => {
  const href = a.getAttribute('href').replace(/\/$/, '') || '/';
  if (href === path || (href !== '/' && path.startsWith(href))) {
    a.classList.add('active-nav-link');
  }
});