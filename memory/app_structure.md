# Kesia Application Structure

- **Frontend (FE):**
    - Path: `kesia-fe/src/pages/`
- **Backend (BE) Controllers:**
    - Path: `sirs-emr-microservice/controller/api/v1/`
- **Peta Microservices:**
    - `sirs-emr-microservice`: ~80% logika klinis (Outpatient, Inpatient, Billing, dll.).
    - `sirs-masterdata-microservice`: Semua master data (Item, Unit, ICD, Doctor).
    - `sirs-bpjs-microservice`: BPJS.
    - `sirs-erp-poster-microservice`: Odoo/ERP sync.
    - `sirs-auth-microservice`: Login, role, user.
- **Catatan:** Beberapa halaman FE routing via API gateway.