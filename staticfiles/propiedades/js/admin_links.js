document.addEventListener('DOMContentLoaded', function() {
    // Mapa de Checkbox Value -> Nombre del Campo URL
    const map = {
        'FB_MARKET': 'url_facebook',
        'FB_PAGE': 'url_meta_ads', // Asumiendo que Meta Enterprise es FB Page
        'INSTAGRAM': 'url_instagram',
        'PORTAL': 'url_portalinmobiliario',
        'YAPO': 'url_yapo',
        'TOCTOC': 'url_toctoc',
        'TERRA_WEB': 'url_terrastudio',
        'OTRA': 'url_otra'
    };

    function toggleFields() {
        // Iteramos sobre las opciones del MultiSelect
        for (const [key, fieldName] of Object.entries(map)) {
            if (!fieldName) continue;

            // Buscamos el checkbox específico (Django les pone ids tipo id_plataformas_publicadas_0, _1, etc)
            // La forma más segura es buscar el input con value=key
            const checkbox = document.querySelector(`input[name="plataformas_publicadas"][value="${key}"]`);
            
            // Buscamos la fila del campo URL correspondiente
            // En Django Admin, cada campo está en un div con clase .field-nombre_del_campo
            const row = document.querySelector(`.field-${fieldName}`);

            if (checkbox && row) {
                if (checkbox.checked) {
                    row.style.display = 'block'; // Mostrar
                } else {
                    row.style.display = 'none'; // Ocultar
                }
            }
        }
    }

    // Ejecutar al inicio (por si vas a editar una ya guardada)
    toggleFields();

    // Escuchar cambios en todos los checkboxes
    const checkboxes = document.querySelectorAll('input[name="plataformas_publicadas"]');
    checkboxes.forEach(cb => {
        cb.addEventListener('change', toggleFields);
    });
});