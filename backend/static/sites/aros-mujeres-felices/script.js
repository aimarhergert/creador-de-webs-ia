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

  document.querySelectorAll('section, .fade-in').forEach(el => {
    el.classList.add('fade-target');
    observer.observe(el);
  });

  const style = document.createElement('style');
  style.textContent = `
    .fade-target { opacity: 0; transform: translateY(30px); transition: opacity 0.7s ease, transform 0.7s ease; }
    .fade-target.visible { opacity: 1; transform: translateY(0); }
  `;
  document.head.appendChild(style);

  const form = document.querySelector('form');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const existing = form.querySelector('.success-msg');
      if (existing) existing.remove();
      const msg = document.createElement('p');
      msg.className = 'success-msg';
      msg.textContent = '¡Gracias! Tu mensaje fue enviado con éxito. 💜';
      msg.style.cssText = 'color:#b5338a;font-weight:bold;margin-top:1rem;text-align:center;';
      form.appendChild(msg);
      form.reset();
      setTimeout(() => msg.remove(), 5000);
    });
  }
});