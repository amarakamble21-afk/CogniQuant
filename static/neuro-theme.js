(() => {
    const storageKey = 'neuroquant.appearance.v1';
    const palettes = ['mint-ocean', 'lavender-plum', 'peach-rose', 'sky-slate'];
    const modes = ['dark', 'light'];
    let appearance = { palette: 'mint-ocean', mode: 'dark' };

    try {
        const stored = JSON.parse(localStorage.getItem(storageKey) || '{}');
        if (palettes.includes(stored.palette)) appearance.palette = stored.palette;
        if (modes.includes(stored.mode)) appearance.mode = stored.mode;
    } catch {
        // Defaults remain available if browser storage is disabled.
    }

    function applyAppearance() {
        const root = document.documentElement;
        root.dataset.palette = appearance.palette;
        root.dataset.mode = appearance.mode;
        document.querySelectorAll('[data-theme-setting="palette"]').forEach(select => {
            select.value = appearance.palette;
        });
        document.querySelectorAll('[data-theme-setting="mode"]').forEach(select => {
            select.value = appearance.mode;
        });
        document.querySelectorAll('meta[name="theme-color"]').forEach(meta => {
            const colors = {
                'mint-ocean': appearance.mode === 'dark' ? '#0b1118' : '#f2f8f5',
                'lavender-plum': appearance.mode === 'dark' ? '#15111f' : '#f7f4fb',
                'peach-rose': appearance.mode === 'dark' ? '#1c1218' : '#fff5f1',
                'sky-slate': appearance.mode === 'dark' ? '#101923' : '#f1f7fb'
            };
            meta.content = colors[appearance.palette];
        });
        updateCharts();
    }

    function updateCharts() {
        if (!window.Chart?.instances) return;
        const chartColors = {
            'mint-ocean': ['#54a9c0', '#59c895', '#bd90db', '#e0a75d', '#db7886', '#8499e3', '#c9aa62'],
            'lavender-plum': ['#94a8f0', '#b38ae3', '#e298c6', '#e7a75c', '#75c6ba', '#d5787d', '#c1a2ed'],
            'peach-rose': ['#70a8c6', '#df8090', '#efaa6b', '#a1bd72', '#b98ad0', '#db9a68', '#cf6572'],
            'sky-slate': ['#55a6d0', '#56b4aa', '#8c9bdd', '#d1a85c', '#d58192', '#79b88b', '#9c84c7']
        }[appearance.palette];
        const foreground = appearance.mode === 'dark' ? '#bdcbd0' : '#405764';
        const grid = appearance.mode === 'dark' ? 'rgba(160,185,194,.18)' : 'rgba(67,101,119,.18)';
        Object.values(window.Chart.instances).forEach(chart => {
            ['x', 'y'].forEach(axisName => {
                const axis = chart.options.scales?.[axisName];
                if (!axis) return;
                if (axis.title) axis.title.color = foreground;
                if (axis.ticks) axis.ticks.color = foreground;
                if (axis.grid) axis.grid.color = grid;
            });
            if (chart.options.plugins?.legend?.labels) {
                chart.options.plugins.legend.labels.color = foreground;
            }
            chart.data.datasets.forEach((dataset, index) => {
                const color = chartColors[index % chartColors.length];
                dataset.borderColor = color;
                dataset.backgroundColor = color;
            });
            chart.update('none');
        });
    }

    applyAppearance();

    document.addEventListener('change', event => {
        const setting = event.target.closest('[data-theme-setting]');
        if (!setting) return;
        if (setting.dataset.themeSetting === 'palette' && palettes.includes(setting.value)) {
            appearance.palette = setting.value;
        }
        if (setting.dataset.themeSetting === 'mode' && modes.includes(setting.value)) {
            appearance.mode = setting.value;
        }
        applyAppearance();
        try {
            localStorage.setItem(storageKey, JSON.stringify(appearance));
        } catch (error) {
            console.error('Could not save appearance preferences.', error);
        }
        document.dispatchEvent(new CustomEvent('neuroquant:appearancechange', { detail: { ...appearance } }));
    });
})();
