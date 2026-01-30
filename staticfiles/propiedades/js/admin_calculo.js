document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. REFERENCIAS A LOS INPUTS (DONDE ESCRIBES) ---
    const inputMoneda = document.getElementById('id_moneda');
    const inputPrecioLista = document.getElementById('id_precio_lista');
    
    // --- 2. REFERENCIAS A LOS OUTPUTS (DONDE SE MUESTRA EL RESULTADO) ---
    // TRUCO CLAVE: Agregamos ".fieldBox" antes para que busque la COLUMNA específica, 
    // y no se confunda con la fila completa.
    const boxUF = document.querySelector('.fieldBox.field-precio_uf .readonly');
    const boxPesos = document.querySelector('.fieldBox.field-precio_pesos_referencia .readonly');

    // Valor UF Base
    let valorUF = 38500; 

    // Obtener UF Real
    fetch('https://mindicador.cl/api/uf')
        .then(response => response.json())
        .then(data => {
            if(data.serie && data.serie.length > 0) {
                valorUF = data.serie[0].valor;
                // Calculamos de nuevo apenas llegue el dato real
                calcular();
            }
        })
        .catch(err => console.log("Usando UF respaldo"));

    // Formateador de números (Estilo Chileno: 1.000.000,00)
    const formateadorPesos = new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP' });
    const formateadorUF = new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    function calcular() {
        // Protección: Si no existen los campos, no hacemos nada
        if (!inputPrecioLista || !inputMoneda) return;

        let precio = parseFloat(inputPrecioLista.value);
        let moneda = inputMoneda.value;

        // Si el precio está vacío, limpiamos los resultados
        if (isNaN(precio)) {
            if(boxUF) boxUF.innerHTML = "-";
            if(boxPesos) boxPesos.innerHTML = "-";
            return;
        }

        let resultadoUF = 0;
        let resultadoPesos = 0;

        // --- LÓGICA DE NEGOCIO (TU REQUERIMIENTO) ---
        if (moneda === 'UF') {
            // SI ELIJO UF:
            // 1. La casilla UF repite el valor exacto (Espejo)
            resultadoUF = precio;
            // 2. La casilla Pesos calcula la conversión (Multiplicar)
            resultadoPesos = Math.round(precio * valorUF);
        } else {
            // SI ELIJO PESOS:
            // 1. La casilla Pesos repite el valor exacto (Espejo)
            resultadoPesos = precio;
            // 2. La casilla UF calcula la conversión (Dividir)
            resultadoUF = (precio / valorUF);
        }

        // --- PINTAR EN PANTALLA (CON PUNTERÍA EXACTA) ---
        // Estilo visual verde neón para confirmar que funciona
        const estilo = 'color: #32cd32; font-weight: bold; margin-left: 8px;';

        // Escribir en la cajita de UF (Izquierda)
        if (boxUF) {
            boxUF.innerHTML = `UF ${formateadorUF.format(resultadoUF)} <span style="${estilo}">(Calc)</span>`;
        }

        // Escribir en la cajita de Pesos (Derecha)
        if (boxPesos) {
            boxPesos.innerHTML = `${formateadorPesos.format(resultadoPesos)} <span style="${estilo}">(Calc)</span>`;
        }
    }

    // Escuchar cambios
    if (inputPrecioLista) inputPrecioLista.addEventListener('input', calcular);
    if (inputMoneda) inputMoneda.addEventListener('change', calcular);
});