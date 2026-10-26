# Spike PF-48: API de IOL

- **Fecha:** 2026-10-25 · **Timebox:** 3 h · **Historia que alimenta:** US-033 (PF-51), precios desde IOL
- **Fuentes:** [documentación](https://api.invertironline.com/Help), [autenticación](https://api.invertironline.com/Help/Autenticacion) y la especificación Swagger `https://api.invertironline.com/v2/swagger`
- **Prueba real:** `scripts/iol_probe.py` (solo lectura, tope duro de 5 llamadas) corrida por el PO con su cuenta; usó 3 llamadas.

## Habilitación
Cuenta comitente abierta, pedido de habilitación por mensaje en el sitio y aceptar los términos en *Mi Cuenta > Personalización > APIs*. Hecho por el PO (acción A4 de la Retro del Sprint 7). Todo lo que se haga por la API impacta en la cuenta real; hay un sandbox solo para órdenes simuladas.

## Autenticación
- `POST https://api.invertironline.com/token`, `application/x-www-form-urlencoded`.
- Primer par de tokens: `grant_type=password`, `username`, `password`.
- Renovación: `grant_type=refresh_token`, `refresh_token`. Devuelve otro par de tokens.
- El bearer token dura **15 minutos** y el refresh token **20 minutos** desde que se emite (`.issued`, `.expires` y `.refreshexpires` en la respuesta, visto por el PO en Postman). Con un job cada 30 minutos el refresh token siempre está vencido: cada corrida pide tokens nuevos con usuario y contraseña.
- Cada request lleva `Authorization: Bearer <token>`.

## Endpoints útiles (solo lectura)
| Endpoint | Qué trae | Llamadas |
|---|---|---|
| `GET /api/v2/Cotizaciones/{tipo}/{pais}/Todos` | Todas las cotizaciones de un tipo: `acciones`, `cedears`, `titulosPublicos`, `obligacionesNegociables`, `aDRs`, `letras`, etc.; país `argentina` o `estados_Unidos` | 1 por tipo |
| `GET /api/v2/Cotizaciones/{tipo}/{panel}/{pais}` | Un panel (por ejemplo, líderes) | 1 por panel |
| `GET /api/v2/{mercado}/Titulos/{simbolo}/Cotizacion` | Un título (`bCBA`, `nYSE`, `nASDAQ`...) con plazo `t0`/`t1`/`t2` | 1 por título |
| `GET /api/v2/portafolio/{pais}` | Tenencias con `cantidad`, `ppc`, `ultimoPrecio`, `valorizado` | 1 |

## Resultado de la prueba
- **Panel completo de acciones:** HTTP 200, **98 títulos en una sola llamada**, cada uno con `simbolo`, `ultimoPrecio`, `moneda` y `fecha`.
- **Cotización de GGAL:** HTTP 200, `ultimoPrecio` 6235 en `peso_Argentino`.
- **Portafolio:** HTTP 200, sin posiciones (la cuenta no tiene tenencias), así que su contenido no se pudo ver con datos.
- **Headers de límite o de cupo restante:** ninguno en las tres respuestas.

## Límite de 25.000 llamadas por mes
- **No está en la documentación pública ni viene en los headers.** No se puede saber desde la API cuánto queda; la única defensa es un contador propio (criterio de US-033).
- Supuesto prudente: la renovación del token cuenta como llamada.

### Presupuesto
Cada 30 minutos de 11 a 17 h en días hábiles son unas **286 corridas por mes**, y cada corrida renueva el token (pasan más de 15 minutos entre una y otra).

| Estrategia | Llamadas por corrida | Por mes | Del límite |
|---|---|---|---|
| Una llamada por instrumento (68 instrumentos) | 69 | ~19.700 | 79 % |
| Paneles completos por tipo (hasta 4 tipos) | 5 | ~1.430 | 6 % |
| **Portafolio** | **2** | **~570** | **2 %** |

## Decisión para US-033
Decisiones del PO después de la prueba:
1. **Solo IOL y el portafolio manda:** una comitente se vincula a IOL y sus tenencias y precios salen de `GET /api/v2/portafolio/argentina`. En esa cuenta no se cargan operaciones a mano; la carga manual queda para cuentas que no son de IOL.
2. **Presupuesto:** 1 llamada de autenticación y 1 de portafolio por corrida, unas 570 por mes (2 % del límite). Los paneles por tipo quedan como alternativa si hiciera falta el precio de algo que no está en la cartera.
3. Contador mensual persistido con corte al 80 % (20.000).
4. Usuario y contraseña de IOL guardados cifrados (US-032), porque el refresh token no sobrevive entre corridas.
5. **Órdenes de compra y venta:** la idea es enviarlas a IOL más adelante, probando primero contra el sandbox (US-064). Hasta entonces la integración es de solo lectura.

## Detalles a tener en cuenta
- **Moneda:** el panel la devuelve como código (`"1"`) y la cotización individual como texto (`peso_Argentino`). Hay que mapear los códigos; `"1"` = pesos se confirmó, el código de dólares falta confirmarlo.
- **Fecha sin zona horaria** (`2026-10-23T17:00:03.727`): se interpreta en hora de Buenos Aires.
- **Bonos y ONs:** el precio de `titulosPublicos` y `obligacionesNegociables` debería ser cada 100 de valor nominal (coincide con `quote_unit`); confirmarlo con una tenencia real.
- **Rotación del refresh token:** no se vio si IOL entrega uno nuevo al renovar; con el diseño de arriba no hace falta, porque cada corrida usa usuario y contraseña.

## Preguntas abiertas
- Cómo cuenta IOL las 25.000 llamadas (si `/token` suma y qué pasa al pasarlas): confirmarlo con IOL.
- Contenido del portafolio con tenencias reales (la cuenta de la prueba estaba vacía).
