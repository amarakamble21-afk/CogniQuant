(() => {
    const canvas = document.getElementById('pixel-brain');
    if (!(canvas instanceof HTMLCanvasElement)) return;
    const context = canvas.getContext('2d');
    if (!context) return;

    const cell = 4;
    const neurons = [
        { soma: [30, 42], branches: [[[30, 42], [18, 42], [18, 30], [10, 30]], [[30, 42], [18, 42], [18, 54], [10, 54]], [[30, 42], [34, 30], [34, 22]]] },
        { soma: [164, 38], branches: [[[164, 38], [176, 38], [176, 26], [184, 26]], [[164, 38], [176, 38], [176, 50], [184, 50]], [[164, 38], [160, 26], [160, 18]]] },
        { soma: [34, 104], branches: [[[34, 104], [22, 104], [22, 92], [14, 92]], [[34, 104], [22, 104], [22, 116], [14, 116]], [[34, 104], [42, 116], [42, 124]]] },
        { soma: [158, 106], branches: [[[158, 106], [174, 106], [174, 94], [182, 94]], [[158, 106], [174, 106], [174, 118], [182, 118]], [[158, 106], [150, 118], [150, 126]]] }
    ];
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function draw(time) {
        context.clearRect(0, 0, canvas.width, canvas.height);
        context.imageSmoothingEnabled = false;

        for (let y = 20; y < 128; y += cell) {
            for (let x = 36; x < 156; x += cell) {
                const dx = (x + cell / 2 - 96) / 59;
                const dy = (y + cell / 2 - 72) / 52;
                const lobe = Math.pow(Math.abs(dx), 2.15) + Math.pow(Math.abs(dy), 1.9);
                if (lobe >= 1.08 || (y > 100 && Math.abs(dx) > 0.72)) continue;

                const center = Math.abs(x + cell / 2 - 96) < 4;
                const groove = !center && (
                    (x > 52 && x < 72 && y > 42 && y < 90 && x % 20 === 8) ||
                    (x > 116 && x < 140 && y > 42 && y < 90 && x % 20 === 12) ||
                    (y > 32 && y < 50 && x % 24 === 12)
                );
                context.fillStyle = center ? '#74cfa9' : groove ? '#4f9e83' : ((x + y) % 3 === 0 ? '#a8f2d1' : '#83ddb6');
                context.fillRect(x, y, cell - 1, cell - 1);
            }
        }

        neurons.forEach((neuron, index) => {
            const pulse = reducedMotion ? 0.72 : 0.48 + 0.48 * (0.5 + 0.5 * Math.sin(time / 540 + index * 1.7));
            context.globalAlpha = pulse;
            context.strokeStyle = '#8cf6dc';
            context.lineWidth = 3;
            context.lineCap = 'square';
            neuron.branches.forEach(branch => {
                context.beginPath();
                branch.forEach(([x, y], point) => {
                    if (point === 0) context.moveTo(x, y);
                    else context.lineTo(x, y);
                });
                context.stroke();
                const [x, y] = branch[branch.length - 1];
                context.fillStyle = '#c1ffe8';
                context.fillRect(x - 2, y - 2, 5, 5);
            });
            context.fillStyle = '#baffdf';
            context.fillRect(neuron.soma[0] - 4, neuron.soma[1] - 4, 8, 8);
        });
        context.globalAlpha = 1;

        if (!reducedMotion) window.requestAnimationFrame(draw);
    }

    draw(0);
})();
