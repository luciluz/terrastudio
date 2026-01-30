document.addEventListener('DOMContentLoaded', function() {
    const map = {
        'FB_MARKET': 'url_facebook',
        'FB_PAGE': 'url_meta_ads',
        'INSTAGRAM': 'url_instagram',
        'PORTAL': 'url_portalinmobiliario',
        'YAPO': 'url_yapo',
        'TOCTOC': 'url_toctoc',
        'TERRA_WEB': 'url_terrastudio',
        'OTRA': 'url_otra'
    };

    function toggleFields() {
        for (const [key, fieldName] of Object.entries(map)) {
            if (!fieldName) continue;
            const checkbox = document.querySelector(`input[name="plataformas_publicadas"][value="${key}"]`);
            const row = document.querySelector(`.field-${fieldName}`);

            if (checkbox && row) {
                if (checkbox.checked) {
                    row.style.display = 'block';
                } else {
                    row.style.display = 'none';
                }
            }
        }
    }

    toggleFields();
    const checkboxes = document.querySelectorAll('input[name="plataformas_publicadas"]');
    checkboxes.forEach(cb => {
        cb.addEventListener('change', toggleFields);
    });
});