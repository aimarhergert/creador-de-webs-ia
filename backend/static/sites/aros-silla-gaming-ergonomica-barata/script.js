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

  document.querySelectorAll('section, .fade-in, .card, .feature, .product').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
  });

  document.addEventListener('animationend', () => {});

  document.querySelectorAll('.visible').forEach(el => {
    el.style.opacity = '1';
    el.style.transform = 'translateY(0)';
  });

  const style = document.createElement('style');
  style.textContent = '.visible { opacity: 1 !important; transform: translateY(0) !important; }';
  document.head.appendChild(style);

  const form = document.querySelector('form');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const success = document.createElement('div');
      success.textContent = '¡Gracias! Tu mensaje ha sido enviado correctamente. Nos pondremos en contacto contigo pronto.';
      success.style.cssText = 'background:#2ecc71;color:#fff;padding:16px 24px;border-radius:8px;margin-top:16px;font-weight:600;text-align:center;';
      this.style.display = 'none';
      this.parentNode.insertBefore(success, this.nextSibling);
      setTimeout(() => {
        success.remove();
        this.reset();
        this.style.display = '';
      }, 5000);
    });
  }
});