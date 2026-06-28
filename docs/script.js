// ═══════════════════════════════════════════════════════
//  OmniLauncher-MC Website Scripts
// ═══════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {

    // ─── Navbar scroll effect ─────────────────────────
    const navbar = document.getElementById('navbar');

    const handleScroll = () => {
        if (window.scrollY > 20) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();

    // ─── Mobile nav toggle ───────────────────────────
    const navToggle = document.getElementById('navToggle');
    const navLinks = document.querySelector('.nav-links');

    if (navToggle) {
        navToggle.addEventListener('click', () => {
            navLinks.classList.toggle('open');

            // Animate hamburger
            const spans = navToggle.querySelectorAll('span');
            if (navLinks.classList.contains('open')) {
                spans[0].style.transform = 'rotate(45deg) translateY(7px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(-45deg) translateY(-7px)';
            } else {
                spans[0].style.transform = '';
                spans[1].style.opacity = '';
                spans[2].style.transform = '';
            }
        });

        // Close menu on link click
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                navLinks.classList.remove('open');
                const spans = navToggle.querySelectorAll('span');
                spans[0].style.transform = '';
                spans[1].style.opacity = '';
                spans[2].style.transform = '';
            });
        });
    }

    // ─── Scroll reveal animation ─────────────────────
    const revealElements = document.querySelectorAll(
        '.feature-card, .download-card, .screenshot-window, .alt-install, .section-header'
    );

    revealElements.forEach(el => el.classList.add('reveal'));

    const revealObserver = new IntersectionObserver(
        (entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        },
        {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px',
        }
    );

    revealElements.forEach(el => revealObserver.observe(el));

    // ─── Stagger feature card animations ─────────────
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach((card, i) => {
        card.style.transitionDelay = `${i * 0.1}s`;
    });

    const downloadCards = document.querySelectorAll('.download-card');
    downloadCards.forEach((card, i) => {
        card.style.transitionDelay = `${i * 0.1}s`;
    });

    // ─── Smooth anchor scroll for buttons ────────────
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', (e) => {
            const target = document.querySelector(anchor.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // ─── Parallax on hero (subtle) ───────────────────
    const hero = document.querySelector('.hero-container');

    if (hero && window.matchMedia('(prefers-reduced-motion: no-preference)').matches) {
        window.addEventListener('scroll', () => {
            const scrolled = window.scrollY;
            if (scrolled < 800) {
                hero.style.transform = `translateY(${scrolled * 0.15}px)`;
                hero.style.opacity = Math.max(0, 1 - scrolled / 600);
            }
        }, { passive: true });
    }

    // ─── Detect OS for download highlight ────────────
    const detectOS = () => {
        const ua = navigator.userAgent.toLowerCase();
        if (ua.includes('win')) return 0;
        if (ua.includes('mac')) return 1;
        if (ua.includes('linux')) return 2;
        return 0;
    };

    const osIndex = detectOS();
    const dlCards = document.querySelectorAll('.download-card');
    if (dlCards[osIndex]) {
        dlCards[osIndex].style.borderColor = 'rgba(108, 59, 245, 0.5)';
        dlCards[osIndex].style.background = 'rgba(108, 59, 245, 0.05)';

        // Add "Recommended" badge
        const badge = document.createElement('div');
        badge.textContent = '✦ Recommended for you';
        badge.style.cssText = `
            font-size: 11px;
            font-weight: 600;
            color: #6C3BF5;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        `;
        dlCards[osIndex].insertBefore(badge, dlCards[osIndex].firstChild);
    }

    console.log(
        '%c⬡ OmniLauncher-MC %cby OmniNodeCo',
        'color: #6C3BF5; font-weight: bold; font-size: 16px;',
        'color: #94A3B8; font-size: 12px;'
    );
});