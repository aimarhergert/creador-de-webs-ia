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
      let successMsg = document.querySelector('.form-success');
      if (!successMsg) {
        successMsg = document.createElement('p');
        successMsg.className = 'form-success';
        successMsg.style.cssText = 'color:#c9a84c;font-weight:bold;margin-top:1rem;text-align:center;';
        form.parentNode.insertBefore(successMsg, form.nextSibling);
      }
      successMsg.textContent = '¡Gracias! Nos pondremos en contacto contigo pronto.';
      form.reset();
      successMsg.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
  }
});