document.addEventListener('DOMContentLoaded', function() {
    
    const inputMoneda = document.getElementById('id_moneda');
    const inputPrecioLista = document.getElementById('id_precio_lista');
    const boxUF = document.querySelector('.fieldBox.field-precio_uf .readonly');
    const boxPesos = document.querySelector('.fieldBox.field-precio_pesos_referencia .readonly');

    let valorUF = 38500; 

    fetch('https://mindicador.cl/api/uf')
        .then(response => response.json())
        .then(data => {
            if(data.serie && data.serie.length > 0) {
                valorUF = data.serie[0].valor;
                calcular();
            }
        })
        .catch(err => console.log("Usando UF respaldo"));

    const formateadorPesos = new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP' });
    const formateadorUF = new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    function calcular() {
        if (!inputPrecioLista || !inputMoneda) return;

        let precio = parseFloat(inputPrecioLista.value);
        let moneda = inputMoneda.value;

        if (isNaN(precio)) {
            if(boxUF) boxUF.innerHTML = "-";
            if(boxPesos) boxPesos.innerHTML = "-";
            return;
        }

        let resultadoUF = 0;
        let resultadoPesos = 0;

        if (moneda === 'UF') {
            resultadoUF = precio;
            resultadoPesos = Math.round(precio * valorUF);
        } else {
            resultadoPesos = precio;
            resultadoUF = (precio / valorUF);
        }

        const estilo = 'color: #32cd32; font-weight: bold; margin-left: 8px;';

        if (boxUF) {
            boxUF.innerHTML = `UF ${formateadorUF.format(resultadoUF)} <span style="${estilo}">(Calc)</span>`;
        }

        if (boxPesos) {
            boxPesos.innerHTML = `${formateadorPesos.format(resultadoPesos)} <span style="${estilo}">(Calc)</span>`;
        }
    }

    if (inputPrecioLista) inputPrecioLista.addEventListener('input', calcular);
    if (inputMoneda) inputMoneda.addEventListener('change', calcular);
});