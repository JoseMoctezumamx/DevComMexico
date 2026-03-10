# /enterprise-formatter
Activa el modo Enterprise Formatter de InfiniteBit.

Transforma el JSON de request/response proporcionado aplicando:
1. El envelope corporativo IB_
2. La convención de nombres activa en `config/naming_conventions.json`
3. Las reglas definidas en `skills/enterprise_formatter_skill.md`

**Uso:** Proporciona el JSON crudo y el contexto del sistema, el agente generará
el payload formateado listo para validación.

Lee el archivo `skills/enterprise_formatter_skill.md` y aplica todas las reglas
antes de generar el output.
