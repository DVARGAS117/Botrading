# Script para aplicar etiquetas de orden a las issues de Botrading
# Fecha: 13 de noviembre de 2025
# Propósito: Etiquetar issues con orden de prioridad basado en dependencias

# Repositorio
$repo = "DVARGAS117/Botrading"

Write-Host "🏷️  Creando sistema de etiquetas de orden..." -ForegroundColor Cyan
Write-Host ""

# Paso 1: Crear etiquetas de orden (orden-01 a orden-18)
Write-Host "📌 Creando etiquetas orden-01 a orden-18..." -ForegroundColor Yellow

for ($i = 1; $i -le 18; $i++) {
    $label = "orden-{0:D2}" -f $i
    Write-Host "   Creando etiqueta: $label"
    gh label create $label --color "0366d6" --description "Prioridad de implementación: $i" -R $repo 2>$null
}

Write-Host ""

# Paso 2: Crear etiquetas de dependencias
Write-Host "🔗 Creando etiquetas de dependencias..." -ForegroundColor Yellow

gh label create "puede-paralelo" --color "28a745" --description "Puede ejecutarse en paralelo con otros" -R $repo 2>$null
gh label create "bloqueante" --color "d73a49" --description "Bloquea otras tareas" -R $repo 2>$null
gh label create "requiere-validacion" --color "f1a208" --description "Requiere validación especial" -R $repo 2>$null

Write-Host ""

# Paso 3: Aplicar etiquetas a issues específicas
Write-Host "✏️  Aplicando etiquetas a issues..." -ForegroundColor Green
Write-Host ""

# FASE 2: IA y Estrategias
Write-Host "🔵 FASE 2: IA y Estrategias" -ForegroundColor Blue

# ORDEN-1: T10 - Issue #26
Write-Host "   [ORDEN-1] Issue #26 - T10 Construcción de prompt IA"
gh issue edit 26 --add-label "orden-01,bloqueante" -R $repo

# ORDEN-2: T13 - Issue #29
Write-Host "   [ORDEN-2] Issue #29 - T13 Parametrización modelo IA"
gh issue edit 29 --add-label "orden-02" -R $repo

# ORDEN-3: T11 - Issue #27 (VERIFICAR - está cerrado pero in-progress)
Write-Host "   [ORDEN-3] Issue #27 - T11 Registro tokens (VERIFICAR ESTADO)"
# No aplicar etiqueta hasta verificar si realmente está implementado
# gh issue edit 27 --add-label "orden-03,requiere-validacion" -R $repo

# ORDEN-4: T23 - Issue #39
Write-Host "   [ORDEN-4] Issue #39 - T23 Cálculo indicadores"
gh issue edit 39 --add-label "orden-04,puede-paralelo" -R $repo

# ORDEN-5: T24 - Issue #40
Write-Host "   [ORDEN-5] Issue #40 - T24 Generación imágenes"
gh issue edit 40 --add-label "orden-05,puede-paralelo" -R $repo

# ORDEN-6: T14 - Issue #30
Write-Host "   [ORDEN-6] Issue #30 - T14 Apertura dual Market/Limit"
gh issue edit 30 --add-label "orden-06,bloqueante" -R $repo

# ORDEN-7: T15 - Issue #31
Write-Host "   [ORDEN-7] Issue #31 - T15 Comparación Market vs Limit"
gh issue edit 31 --add-label "orden-07" -R $repo

# ORDEN-8: T26 - Issue #42
Write-Host "   [ORDEN-8] Issue #42 - T26 Reevaluación cada 10 min"
gh issue edit 42 --add-label "orden-08,bloqueante" -R $repo

# ORDEN-9: T27 - Issue #43
Write-Host "   [ORDEN-9] Issue #43 - T27 Aplicar decisión SL/TP"
gh issue edit 43 --add-label "orden-09" -R $repo

# ORDEN-10: T12 - Issue #28
Write-Host "   [ORDEN-10] Issue #28 - T12 Contexto conversación"
gh issue edit 28 --add-label "orden-10" -R $repo

# ORDEN-11: T28 - Issue #44
Write-Host "   [ORDEN-11] Issue #44 - T28 Trazabilidad reevaluación"
gh issue edit 44 --add-label "orden-11" -R $repo

# ORDEN-12: T16 - Issue #32
Write-Host "   [ORDEN-12] Issue #32 - T16 Reevaluación dual independiente"
gh issue edit 32 --add-label "orden-12" -R $repo

Write-Host ""

# FASE 3: Persistencia
Write-Host "🟣 FASE 3: Persistencia y Métricas" -ForegroundColor Magenta

# ORDEN-13: T32 - Issue #48
Write-Host "   [ORDEN-13] Issue #48 - T32 Persistencia operaciones"
gh issue edit 48 --add-label "orden-13,bloqueante" -R $repo

# ORDEN-14: T33 - Issue #49
Write-Host "   [ORDEN-14] Issue #49 - T33 Registro consultas IA"
gh issue edit 49 --add-label "orden-14" -R $repo

# ORDEN-15: T34 - Issue #50
Write-Host "   [ORDEN-15] Issue #50 - T34 Consolidación métricas"
gh issue edit 50 --add-label "orden-15" -R $repo

# ORDEN-16: T42 - Issue #58
Write-Host "   [ORDEN-16] Issue #58 - T42 Comparación metodologías"
gh issue edit 58 --add-label "orden-16" -R $repo

Write-Host ""

# FASE 4: Calidad
Write-Host "⚫ FASE 4: Calidad y Validación" -ForegroundColor White

# ORDEN-17: T51 - Issue #67
Write-Host "   [ORDEN-17] Issue #67 - T51 Tests E2E"
gh issue edit 67 --add-label "orden-17" -R $repo

# ORDEN-18: T50 - Issue #66
Write-Host "   [ORDEN-18] Issue #66 - T50 Roadmap y criterios"
gh issue edit 66 --add-label "orden-18" -R $repo

Write-Host ""
Write-Host "✅ Etiquetas aplicadas correctamente!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Resumen:" -ForegroundColor Cyan
Write-Host "   - Etiquetas orden-01 a orden-18 creadas"
Write-Host "   - Etiquetas de dependencias creadas"
Write-Host "   - Issues etiquetadas según orden de implementación"
Write-Host ""
Write-Host "⚠️  ACCIÓN REQUERIDA:" -ForegroundColor Yellow
Write-Host "   - Verificar estado de Issue #27 (T11) - aparece cerrada pero in-progress"
Write-Host ""
Write-Host "🎯 Próximo paso:" -ForegroundColor Green
Write-Host "   Comenzar con ORDEN-1: Issue #26 (T10 - Construcción prompt IA)"
Write-Host ""
