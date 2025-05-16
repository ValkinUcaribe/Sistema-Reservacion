# Sistema_Simuladores
Este repositorio es para el codigo del sistema de reserva para simuladores en la nube de AWS

## Tabla de Contenidos
1. [Descripción General](#descripción-general)
2. [Requisitos Técnicos](#requisitos-técnicos)
3. [Configuración](#configuración)
4. [Arquitectura](#arquitectura)
5. [Endpoints](#endpoints)
6. [Base de Datos](#base-de-datos)
7. [Flujo de Autenticación](#flujo-de-autenticación)
8. [Sistema de Pagos](#sistema-de-pagos)
9. [Reservaciones](#reservaciones)
10. [Administración](#administración)
11. [Despliegue](#despliegue)

---

## Descripción General
Plataforma para reserva de simuladores de vuelo con:

- **Autenticación dual**: Cuentas locales y Google OAuth 2.0
- **Gestión de horarios**: Sistema de reservas con tokens únicos
- **Tienda integrada**: Paquetes de horas y productos físicos
- **Panel administrativo**: CRUD completo para gestión

**Diagrama de componentes**:
```mermaid
graph TD
    A[Frontend] --> B[Backend Flask]
    B --> C[MySQL]
    B --> D[Stripe API]
    B --> E[Google OAuth]
    B --> F[SMTP Server]
