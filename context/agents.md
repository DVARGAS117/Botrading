## ESTE DOCUMENTO CONTIENE LAS REGLAS QUE EL AGENTE SIEMPRE DEBE DE SEGUIR AL MOMENTO DE EMPEZAR A RESOLVER UNA TAREA ASIGNADA POR EL USUARIO.
## NO DEBES OMITIR NINGUNA DE ESTAS REGLAS BAJO NINGUNA CIRCUNSTANCIA.

REGLAS DEL AGENTE:
** SIEMPRE DEBES UTILIZAR LA METODOLOGIA TDD (TEST DRIVEN DEVELOPMENT) PARA DESARROLLAR CUALQUIER TAREA ASIGNADA.
** SIEMPRE DEBES PROPORCIONAR PRUEBAS UNITARIAS PARA CADA FUNCIONALIDAD QUE DESARROLLES.
** SIEMPRE DEBES ASEGURARTE DE QUE TODAS LAS PRUEBAS UNITARIAS PASEN EXITOSAMENTE ANTES DE ENTREGAR EL CÓDIGO.
** SIEMPRE DEBES DOCUMENTAR el código siguiendo el formato de documentación estándar del proyecto (ej. JSDoc, PyDoc) y actualizar los archivos relevantes en la carpeta CONTEXT/DOCUMENTACION.
** SIEMPRE DEBES SEGUIR LAS MEJORES PRÁCTICAS DE PROGRAMACIÓN Y DISEÑO DE SOFTWARE.
** SIEMPRE DEBES ASEGURARTE DE QUE EL CÓDIGO SEA LEGIBLE Y MANTENIBLE.
** SIEMPRE DEBES DE CREAR UNA RAMA NUEVA EN EL REPOSITORIO DE GIT PARA CADA TAREA ASIGNADA. (SIN EXCEPCIONES)
** SIEMPRE DEBES UTILIZAR CONTROL DE VERSIONES PARA CUALQUIER CÓDIGO QUE DESARROLLES.
** SIEMPRE DEBES ASEGURARTE DE QUE EL CÓDIGO CUMPLA CON LOS ESTÁNDARES DE CALIDAD Y SEGURIDAD.
** SIEMPRE DEBES GUIARTE DE LA DOCUMENTACION EXISTENTE EN LA CARPETA CONTEXT/DOCUMENTACION PARA CUALQUIER TAREA ASIGNADA O DUDA QUE TENGAS.
** SIEMPRE DEBES ASEGURARTE DE QUE EL CÓDIGO SEA COMPATIBLE CON LAS TECNOLOGÍAS Y HERRAMIENTAS UTILIZADAS EN EL PROYECTO.
** SIEMPRE DEBES INFORMAR AL USUARIO SI ENCUENTRAS ALGUNA DIFICULTAD O IMPEDIMENTO PARA COMPLETAR LA TAREA ASIGNADA.
** SIEMPRE DEBES ASEGURARTE DE QUE EL CÓDIGO CUMPLA CON LOS REQUERIMIENTOS FUNCIONALES Y NO FUNCIONALES DEL PROYECTO.
** SIEMPRE DEBES vincular el commit final y la Pull Request al número de ticket o issue correspondiente (Ej: "feat: [TICKET-123] Implementación de la función X").

## INSTRUCCIÓN DE INTEGRACIÓN Y FUSIÓN (AL FINALIZAR LA TAREA)

ESTA SECUENCIA DE PASOS DEBE EJECUTARSE AL TERMINAR UNA TAREA Y ANTES DE LA FUSIÓN FINAL. NO SE PERMITE FUSIÓN DIRECTA.

0.  **SELECCIÓN Y MARCAJE:** Antes de cualquier acción, **actualiza el estado del Issue seleccionado a "En Proceso" o "In Progress"** en GitHub CLI. Si el issue ya está en este estado, revierte la selección y pasa al siguiente issue de mayor prioridad.
1.  **FINALIZAR Y RESPALDAR:** Haz un commit local final en tu rama (`ticket-N`) con el trabajo completo y **respalda la rama antes de la integración**: `git push origin ticket-N`
2.  **SINCRONIZAR `desarrollo`:**
    * `git checkout desarrollo`
    * `git pull origin desarrollo`
3.  **INTEGRAR CAMBIOS:**
    * `git checkout ticket-N`
    * `git merge desarrollo` (Para obtener el trabajo de otros agentes y probar compatibilidad).
4.  **CONFLICTOS:** Si hay conflictos de fusión, **detente y resuelve** antes de continuar.
5.  **PRUEBA DE INTEGRACIÓN:** Ejecuta **TODAS las pruebas del proyecto** en la rama `ticket-N`.
6.  **VALIDACIÓN:** Si las pruebas fallan en `ticket-N`, **detente y notifica el error**.
7.  **FUSIÓN FINAL (si las pruebas pasan):**
    * `git checkout desarrollo`
    * `git merge ticket-N`
8.  **PRUEBA DE ESTABILIDAD:** Ejecuta **TODAS las pruebas del proyecto** en la rama `desarrollo`.
9.  **PUSH FINAL (si las pruebas pasan):**
    * `git push origin desarrollo`
    * `git push origin ticket-N`
    * **LIMPIEZA:** Elimina la rama local y remota: `git branch -d ticket-N` y `git push origin --delete ticket-N`
10. **FALLO EN ESTABILIDAD:** Si las pruebas en `desarrollo` fallan, **revierte la fusión con `git revert` y notifica**.
11. **VERIFICACIÓN HUMANA:** Si la integración es exitosa (pasos 1 a 10 completos), **DEBES SOLICITAR CONSENTIMIENTO EXPLÍCITO** al usuario antes de cerrar el *ticket* en GitHub CLI. La tarea solo se marca como cerrada tras la confirmación del usuario.