document.addEventListener('DOMContentLoaded', () => {

  const navbar = document.getElementById('navbar');
  const mobileMenuBtn = document.getElementById('mobile-menu-btn');
  const mobileMenu = document.getElementById('mobile-menu');
  const menuIconOpen = document.getElementById('menu-icon-open');
  const menuIconClose = document.getElementById('menu-icon-close');

  // 1. NAVBAR SCROLL EFFECT
  const navClasses = ['navbar-scrolled', 'bg-slate-950/90', 'backdrop-blur-xl', 'shadow-xl', 'shadow-black/20'];
  window.addEventListener('scroll', () => {
    if (window.scrollY > 10) {
      navbar?.classList.add(...navClasses);
    } else {
      navbar?.classList.remove(...navClasses);
    }
  }, { passive: true });

  // 2. MOBILE MENU TOGGLE
  const closeMobileMenu = () => {
    mobileMenu?.classList.add('hidden');
    menuIconOpen?.classList.remove('hidden');
    menuIconClose?.classList.add('hidden');
  };

  mobileMenuBtn?.addEventListener('click', (e) => {
    e.stopPropagation();
    const isHidden = mobileMenu?.classList.toggle('hidden');
    menuIconOpen?.classList.toggle('hidden', !isHidden);
    menuIconClose?.classList.toggle('hidden', isHidden);
  });

  document.addEventListener('click', (e) => {
    if (mobileMenu && !mobileMenu.contains(e.target) && e.target !== mobileMenuBtn) {
      closeMobileMenu();
    }
  });

  mobileMenu?.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMobileMenu));

  // 3. SCROLL ANIMATIONS
  const animObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const siblings = el.parentElement?.querySelectorAll('[data-animate]');
        if (siblings) {
          const idx = Array.from(siblings).indexOf(el);
          if (idx > 0) el.style.transitionDelay = `${idx * 100}ms`;
        }
        el.classList.add('is-visible');
        animObserver.unobserve(el);
      }
    });
  }, { threshold: 0.2 });

  document.querySelectorAll('[data-animate]').forEach(el => animObserver.observe(el));

  // 4. FAQ ACCORDION
  document.querySelectorAll('.faq-item').forEach(item => {
    const btn = item.querySelector('button');
    const answer = item.querySelector('.faq-answer');
    if (!btn || !answer) return;
    answer.style.height = '0';
    answer.style.overflow = 'hidden';
    answer.style.transition = 'height 300ms ease';

    btn.addEventListener('click', () => {
      const isOpen = item.classList.contains('faq-open');
      document.querySelectorAll('.faq-item.faq-open').forEach(open => {
        open.classList.remove('faq-open');
        const a = open.querySelector('.faq-answer');
        const b = open.querySelector('button');
        if (a) a.style.height = '0';
        if (b) b.querySelector('.faq-icon') && (b.querySelector('.faq-icon').textContent = '+');
      });
      if (!isOpen) {
        item.classList.add('faq-open');
        answer.style.height = answer.scrollHeight + 'px';
        const icon = btn.querySelector('.faq-icon');
        if (icon) icon.textContent = '×';
      }
    });
  });

  // 5. STATS COUNTER ANIMATION
  const animatedStats = new Set();
  const easeOut = t => 1 - Math.pow(1 - t, 3);

  const animateCounter = (el) => {
    const target = parseFloat(el.dataset.target) || 0;
    const suffix = el.dataset.suffix || '';
    const duration = 1500;
    const start = performance.now();
    const isDecimal = target % 1 !== 0;

    const tick = (now) => {
      const elapsed = Math.min((now - start) / duration, 1);
      const value = easeOut(elapsed) * target;
      el.textContent = (isDecimal ? value.toFixed(1) : Math.floor(value)) + suffix;
      if (elapsed < 1) requestAnimationFrame(tick);
      else el.textContent = (isDecimal ? target.toFixed(1) : target) + suffix;
    };
    requestAnimationFrame(tick);
  };

  const statObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting && !animatedStats.has(entry.target)) {
        animatedStats.add(entry.target);
        animateCounter(entry.target);
        statObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  document.querySelectorAll('.stat-number').forEach(el => statObserver.observe(el));

  // 6. SMOOTH SCROLL
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      const id = anchor.getAttribute('href');
      if (id === '#') return;
      const target = document.querySelector(id);
      if (!target) return;
      e.preventDefault();
      const top = target.getBoundingClientRect().top + window.scrollY - 80;
      window.scrollTo({ top, behavior: 'smooth' });
    });
  });

  // 7. CONTACT FORM HANDLER
  const contactForm = document.getElementById('contact-form');
  const formSuccess = document.getElementById('form-success');

  contactForm?.addEventListener('submit', (e) => {
    e.preventDefault();
    const name = contactForm.querySelector('[name="name"]')?.value.trim();
    const email = contactForm.querySelector('[name="email"]')?.value.trim();
    const message = contactForm.querySelector('[name="message"]')?.value.trim();
    if (!name || !email || !message) return;

    const btn = contactForm.querySelector('button[type="submit"]');
    const original = btn?.textContent;
    if (btn) { btn.disabled = true; btn.textContent = 'Enviando...'; }

    setTimeout(() => {
      contactForm.style.display = 'none';
      if (formSuccess) {
        formSuccess.textContent = '¡Gracias por contactarnos! Hemos recibido tu mensaje y te responderemos en un plazo de 24-48 horas hábiles. Nos pondremos en contacto contigo a la brevedad posible.';
        formSuccess.classList.remove('hidden');
        formSuccess.style.animation = 'slideIn 0.5s ease forwards';
      }
      if (btn) { btn.disabled = false; btn.textContent = original; }
    }, 1200);
  });

  // 8. NEWSLETTER FORM HANDLER
  const newsletterForm = document.getElementById('newsletter-form');

  newsletterForm?.addEventListener('submit', (e) => {
    e.preventDefault();
    const emailInput = newsletterForm.querySelector('[type="email"]');
    if (!emailInput?.value.trim()) return;

    const btn = newsletterForm.querySelector('button[type="submit"]');
    const original = btn?.textContent;
    if (btn) { btn.disabled = true; btn.textContent = 'Suscribiendo...'; }

    setTimeout(() => {
      let msg = newsletterForm.querySelector('.newsletter-success');
      if (!msg) {
        msg = document.createElement('p');
        msg.className = 'newsletter-success text-green-400 text-sm mt-2 font-medium';
        newsletterForm.appendChild(msg);
      }
      msg.textContent = '¡Suscripción confirmada! Recibirás nuestras novedades pronto.';
      emailInput.value = '';
      if (btn) { btn.disabled = false; btn.textContent = original; }
    }, 1200);
  });

  // 9. ACTIVE NAV LINK
  const path = window.location.pathname.split('/').filter(Boolean).pop() || 'index.html';
  document.querySelectorAll('nav a[href]').forEach(link => {
    const href = link.getAttribute('href').split('/').filter(Boolean).pop() || 'index.html';
    if (href === path) link.classList.add('active-nav-link');
  });

});