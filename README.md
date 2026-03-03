# Sistema de trazabilidad walk-in (MVP open source)

Aplicación rápida para validar en campo un esquema de **ticket por candidato** con trazabilidad en tiempo real.

## 1) Diseño de base de datos (Microsoft Lists)

### Lista principal: `RecruitmentTickets`

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---:|---|
| TicketID | Texto (único) | Sí | Identificador del ticket (`GT-WALK-0001`) |
| CandidateName | Texto | Sí | Nombre completo |
| Phone | Texto | No | Contacto |
| Position | Texto | Sí | Vacante |
| Site | Opción | Sí | Ubicación (ej. Guatemala) |
| Recruiter | Persona/Grupo | Sí | Reclutador asignado |
| Status | Opción | Sí | Etapa actual |
| CurrentOwner | Opción | Sí | Dueño operativo actual |
| CreatedAt | Fecha/hora | Sí | Inicio del ticket |
| UpdatedAt | Fecha/hora | Sí | Último movimiento |
| TS_Recepcion | Fecha/hora | Sí | Inicio de recepción |
| TS_PreAssessmentStart | Fecha/hora | No | Inicio pre-assessment |
| TS_TestingStart | Fecha/hora | No | Inicio testing |
| TS_TestingEnd | Fecha/hora | No | Fin testing |
| TS_DecisionStart | Fecha/hora | No | Inicio decisión |
| TS_ComplianceStart | Fecha/hora | No | Inicio compliance |
| TS_Closed | Fecha/hora | No | Cierre (contratado/no contratado) |
| TS_Abandono | Fecha/hora | No | Marca de abandono |
| AbandonReason | Opción + texto | No | Motivo abandono |
| Notes | Texto largo | No | Observaciones |

### Catálogo de estados
1. Recepción
2. Pre-assessment
3. Testing
4. Waiting room post-testing
5. Decisión final
6. Compliance
7. Contratado (terminal)
8. No contratado (terminal)
9. Abandonó (terminal)

### Lógica de ownership por etapa
- Recepción → **Recepción**
- Pre-assessment / Waiting room post-testing / Decisión final → **Reclutador**
- Testing → **Testing POC**
- Compliance / Contratado → **Compliance**
- No contratado → **Reclutador**
- Abandonó → **Recepción**

---

## 2) Flujo operativo por rol

| Rol | Acciones/“botones” | Timestamp que se actualiza | Transiciones permitidas |
|---|---|---|---|
| Recepción | Crear ticket, enviar a pre-assessment, marcar abandono | `TS_Recepcion`, `UpdatedAt` | Recepción → Pre-assessment / Abandonó |
| Reclutador | Iniciar pre-assessment, enviar a testing, decisión final | `TS_PreAssessmentStart`, `TS_DecisionStart`, `UpdatedAt` | Pre-assessment → Testing / No contratado / Abandonó; Waiting room → Decisión final |
| Testing POC | Iniciar y cerrar testing | `TS_TestingStart`, `TS_TestingEnd`, `UpdatedAt` | Testing → Waiting room post-testing / Abandonó |
| Compliance | Iniciar compliance, cerrar contratado/no contratado | `TS_ComplianceStart`, `TS_Closed`, `UpdatedAt` | Compliance → Contratado / No contratado / Abandonó |

Regla: **cada cambio de estado actualiza `UpdatedAt` y `CurrentOwner`**.

---

## 3) Interfaz (Teams/SharePoint + MVP open source)

### Vistas mínimas por rol
- Recepción: TicketID, CandidateName, Status, CurrentOwner, UpdatedAt.
- Reclutador: CandidateName, Recruiter, Status, UpdatedAt, Position.
- Testing: CandidateName, Status, UpdatedAt.
- Compliance: CandidateName, Status, TS_ComplianceStart, TS_Closed.
- Supervisor: todas + métricas de espera.

### Minimización de errores
- Botones con transiciones válidas (sin edición libre de `Status`).
- Campos obligatorios al crear ticket.
- Listas desplegables para motivos de abandono.
- Alertas SLA automáticas.

### Power Apps opcional
- App Canvas embebida en Teams para UI móvil y de escritorio.
- Formulario único por rol con botones de transición.

---

## 4) Automatizaciones (Power Automate)

1. **Asignación balanceada de reclutador**
   - Trigger: ticket nuevo.
   - Lógica: contar tickets activos por reclutador y asignar al de menor carga.

2. **Alertas SLA de espera**
   - Si `Now - UpdatedAt > SLA etapa` enviar notificación en Teams al owner y supervisor.

3. **Notificaciones entre equipos**
   - Cambio a Testing → mensaje al canal Testing.
   - Cambio a Compliance → mensaje al canal Compliance.

4. **Cierre y seguimiento**
   - Fin de día: tickets abiertos sin movimiento > X min pasan a “Seguimiento día siguiente”.

---

## 5) Dashboard Power BI

### KPIs
- Candidatos en sitio (activos)
- Tiempo promedio total por candidato
- Tiempo promedio de espera por etapa
- Abandono %
- Conversión a contratación %
- Productividad por reclutador

### Visualizaciones
- Tarjetas KPI en tiempo real
- Embudo por etapa
- Barras de tiempo promedio por etapa
- Heatmap por hora del día (llegadas/abandono)
- Tabla de tickets con SLA en riesgo

### Cálculos
- **Espera** = tiempo entre `UpdatedAt` y atención siguiente.
- **Servicio** = tiempo activo en etapa atendida.
- **Tiempo total** = `TS_Closed` (o now) - `CreatedAt`.
- **Cuello de botella** = etapa con mayor espera promedio y mayor volumen en cola.

---

## 6) Reglas operativas

- **Dueño actual**: rol responsable de ejecutar la siguiente acción obligatoria.
- **Espera**: candidato sin atención activa en una etapa.
- **Servicio**: etapa donde un actor está atendiendo al candidato.
- **Abandono**: salida sin cierre contractual; requiere motivo.
- **Cierre diario**: corte fijo (ej. 18:00), revisión de abiertos, reasignación y plan de seguimiento.

---

## 7) Plan de implementación (<2 semanas)

### Fase piloto (Día 1 a 5)
- Configurar Lists y vistas por rol.
- Activar 2 flujos críticos (asignación + alertas SLA).
- Capacitación express de 45 minutos.
- Pilotear en 1 sede (Guatemala).

### Escalamiento (Día 6 a 10)
- Ajuste de campos y SLAs.
- Publicar dashboard Power BI en Teams.
- Replicar plantilla a nuevas sedes/países.

### Riesgos comunes y mitigación
- Baja adopción → champions por turno + métricas visibles.
- Mala calidad de datos → validaciones obligatorias + auditoría diaria.
- Saturación de Testing → alerta temprana por cola.

---

## 8) IA opcional (alto valor)

### Casos prácticos
- Resumen automático de turno: cuello de botella, abandono y causa principal.
- Recomendación de staffing por franja horaria.
- Priorización de tickets en riesgo de abandono.

### Prompts ejemplo para supervisores
- "Resume el turno de hoy en 5 bullets: volumen, abandono, SLA roto y acción inmediata."
- "¿Qué etapa fue cuello de botella hoy y qué cambio operativo sugieres para mañana?"

### Automatización de insights
- Power Automate + Copilot: resumen diario publicado en Teams.

---

## 9) App open source incluida en este repositorio

### Stack
- **Streamlit** (UI operativa + dashboard)
- **Pandas** (métricas)
- **Plotly** (gráficas)
- Persistencia local CSV (`data/candidates.csv`)

### Ejecutar
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### Qué cubre el MVP
- Ticket por candidato
- Timestamps automáticos por etapa
- Reglas de transición de estado
- Ownership automático por etapa
- KPI y detección básica de cuellos de botella
- Asignación balanceada de reclutador en ingreso
