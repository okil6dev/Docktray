// ─── Scroll Reveal ───────────────────────────────
const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        // Stagger sibling cards
        const siblings = [...entry.target.parentElement.children];
        const idx = siblings.indexOf(entry.target);
        setTimeout(() => {
          entry.target.classList.add('revealed');
        }, idx * 80);
        revealObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.12 }
);

document.querySelectorAll('[data-reveal]').forEach(el => revealObserver.observe(el));

// ─── Nav scroll effect ────────────────────────────
const nav = document.getElementById('nav');
window.addEventListener('scroll', () => {
  if (window.scrollY > 40) {
    nav.style.background = 'rgba(8,8,16,0.75)';
  } else {
    nav.style.background = 'rgba(8,8,16,0.5)';
  }
}, { passive: true });

// ─── Dock app hover ripple ────────────────────────
document.querySelectorAll('.dock-app').forEach(app => {
  app.addEventListener('click', () => {
    app.style.transform = 'scale(0.92)';
    setTimeout(() => { app.style.transform = ''; }, 150);
  });
});

// ─── Parallax orbs on mouse move ─────────────────
document.addEventListener('mousemove', (e) => {
  const cx = window.innerWidth / 2;
  const cy = window.innerHeight / 2;
  const dx = (e.clientX - cx) / cx;
  const dy = (e.clientY - cy) / cy;

  const orbs = document.querySelectorAll('.orb');
  const factors = [18, 12, 20, 10];
  orbs.forEach((orb, i) => {
    const f = factors[i] || 15;
    orb.style.transform = `translate(${dx * f}px, ${dy * f}px)`;
  });
}, { passive: true });

// ─── Smooth active nav highlight ─────────────────
const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('.nav-links a');

const sectionObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        navLinks.forEach(link => {
          link.style.color = '';
          if (link.getAttribute('href') === '#' + entry.target.id) {
            link.style.color = '#a5b4fc';
          }
        });
      }
    });
  },
  { threshold: 0.4 }
);

sections.forEach(s => sectionObserver.observe(s));
