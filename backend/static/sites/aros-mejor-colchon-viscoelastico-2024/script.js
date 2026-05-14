document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });

  document.querySelectorAll('section, .card, .product, .review, .feature').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
  });

  document.addEventListener('animationend', () => {});

  document.documentElement.style.setProperty('--fade-ready', '1');

  const style = document.createElement('style');
  style.textContent = '.visible { opacity: 1 !important; transform: translateY(0) !important; }';
  document.head.appendChild(style);

  const form = document.querySelector('form');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const success = document.createElement('div');
      success.textContent = '¡Gracias! Tu mensaje ha sido enviado correctamente.';
      success.style.cssText = 'background:#28a745;color:#fff;padding:12px 20px;border-radius:6px;margin-top:16px;font-weight:bold;text-align:center;';
      const existing = form.querySelector('.form-success');
      if (existing) existing.remove();
      success.classList.add('form-success');
      form.appendChild(success);
      form.reset();
      setTimeout(() => success.remove(), 5000);
    });
  }

  window.addEventListener('scroll', () => {
    const scrollTop = window.scrollY;
    const navbar = document.querySelector('nav, header, .navbar');
    if (navbar) {
      navbar.style.boxShadow = scrollTop > 50 ? '0 2px 12px rgba(0,0,0,0.15)' : '';
    }
  });
});