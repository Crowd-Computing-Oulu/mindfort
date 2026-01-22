// Intersection Observer for Scroll Reveals
document.addEventListener('DOMContentLoaded', () => {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('reveal-active');
            }
        });
    }, { threshold: 0.05 });

    document.querySelectorAll('.reveal').forEach(el => {
        observer.observe(el);
    });
});
