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

  document.querySelectorAll('section, .card, .product-item, .feature, .review').forEach(el => {
    el.classList.add('fade-in');
    observer.observe(el);
  });

  const style = document.createElement('style');
  style.textContent = `
    .fade-in { opacity: 0; transform: translateY(24px); transition: opacity 0.6s ease, transform 0.6s ease; }
    .fade-in.visible { opacity: 1; transform: translateY(0); }
  `;
  document.head.appendChild(style);

  const form = document.querySelector('form');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const existing = form.querySelector('.success-message');
      if (existing) existing.remove();
      const msg = document.createElement('p');
      msg.className = 'success-message';
      msg.textContent = '¡Gracias! Te enviaremos las mejores ofertas de auriculares bluetooth pronto.';
      msg.style.cssText = 'color:#2ecc71;font-weight:600;margin-top:12px;text-align:center;';
      form.appendChild(msg);
      form.reset();
      setTimeout(() => msg.remove(), 5000);
    });
  }

  document.querySelectorAll('.btn-cta, .buy-button, [data-product]').forEach(btn => {
    btn.addEventListener('click', function () {
      this.style.transform = 'scale(0.96)';
      setTimeout(() => { this.style.transform = ''; }, 150);
    });
  });
});