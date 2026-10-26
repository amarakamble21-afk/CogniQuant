(() => {
    const canvas = document.querySelector('.neural-field');
    if (!canvas) return;
    const context = canvas.getContext('2d');
    if (!context) return;

    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let width = 0;
    let height = 0;
    let points = [];
    let animationFrame = 0;
    let lastFrame = 0;

    function resize() {
        const scale = Math.min(window.devicePixelRatio || 1, 1.5);
        width = window.innerWidth;
        height = window.innerHeight;
        canvas.width = Math.round(width * scale);
        canvas.height = Math.round(height * scale);
        context.setTransform(scale, 0, 0, scale, 0, 0);
        const count = Math.min(58, Math.max(24, Math.floor(width * height / 26000)));
        points = Array.from({ length: count }, () => ({
            x: Math.random() * width,
            y: Math.random() * height,
            dx: (Math.random() - .5) * .16,
            dy: (Math.random() - .5) * .16,
            radius: Math.random() * 1.5 + .7
        }));
        draw(0);
    }

    function draw(timestamp) {
        if (timestamp - lastFrame < 48 && !reducedMotion) {
            animationFrame = requestAnimationFrame(draw);
            return;
        }
        lastFrame = timestamp;
        context.clearRect(0, 0, width, height);
        for (let index = 0; index < points.length; index++) {
            const point = points[index];
            if (!reducedMotion) {
                point.x += point.dx;
                point.y += point.dy;
                if (point.x < 0 || point.x > width) point.dx *= -1;
                if (point.y < 0 || point.y > height) point.dy *= -1;
            }
            for (let otherIndex = index + 1; otherIndex < points.length; otherIndex++) {
                const other = points[otherIndex];
                const distance = Math.hypot(point.x - other.x, point.y - other.y);
                if (distance < 150) {
                    context.strokeStyle = `rgba(112, 239, 196, ${(1 - distance / 150) * .24})`;
                    context.lineWidth = .7;
                    context.beginPath();
                    context.moveTo(point.x, point.y);
                    context.lineTo(other.x, other.y);
                    context.stroke();
                }
            }
            context.fillStyle = 'rgba(160, 255, 220, .7)';
            context.shadowColor = 'rgba(86, 244, 190, .72)';
            context.shadowBlur = 11;
            context.beginPath();
            context.arc(point.x, point.y, point.radius, 0, Math.PI * 2);
            context.fill();
            context.shadowBlur = 0;
        }
        if (!reducedMotion) animationFrame = requestAnimationFrame(draw);
    }

    window.addEventListener('resize', resize, { passive: true });
    window.addEventListener('pagehide', () => cancelAnimationFrame(animationFrame), { once: true });
    resize();
})();
