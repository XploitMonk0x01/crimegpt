# Document Compliance Matrix

This matrix maps Problem Statement required documents to current CrimeGPT implementation touchpoints and demo proof artifacts.

| PS Required Document | DocumentType Enum | Backend Route/Service | Frontend UI | Required Core Inputs | Sample Output Proof |
|---|---|---|---|---|---|
| Purvani Chargesheet | `chargesheet` | `backend/app/routes/documentRoutes.py`, `backend/app/services/documentService.py` | `frontend/src/components/DocumentGenerator.jsx` | FIR narrative, accused details, sections, IO details | `docs/samples/chargesheet-sample.md` |
| Medical Treatment Letter | `medical_letter` | `backend/app/routes/documentRoutes.py`, `backend/app/services/documentService.py` | `frontend/src/components/DocumentGenerator.jsx` | victim details, injuries, hospital details, case ref | `docs/samples/medical-letter-sample.md` |
| Remand Request Letter (Police Custody) | `remand_request` | `backend/app/routes/documentRoutes.py`, `backend/app/services/documentService.py` | `frontend/src/components/DocumentGenerator.jsx` | accused details, grounds for custody, case sections | `docs/samples/remand-request-sample.md` |
| Seizure Receipt | `seizure_receipt` | `backend/app/routes/documentRoutes.py`, `backend/app/services/documentService.py` | `frontend/src/components/DocumentGenerator.jsx` | seized items list, place/date/time, witness details | `docs/samples/seizure-receipt-sample.md` |
| Court Custody Letter | `court_custody_letter` | `backend/app/routes/documentRoutes.py`, `backend/app/services/documentService.py` | `frontend/src/components/DocumentGenerator.jsx` | accused details, custody transfer details, court info | `docs/samples/court-custody-sample.md` |
| Accused Panchanama | `accused_panchanama` | `backend/app/routes/documentRoutes.py`, `backend/app/services/documentService.py` | `frontend/src/components/DocumentGenerator.jsx` | panch witness details, accused observation memo | `docs/samples/accused-panchanama-sample.md` |
| Accused Face Identification Form | `face_id_form` | `backend/app/routes/documentRoutes.py`, `backend/app/services/documentService.py` | `frontend/src/components/DocumentGenerator.jsx` | accused biometric/face descriptors, witness identification | `docs/samples/face-id-form-sample.md` |

## Compliance Notes
- Document types are aligned with `DocumentType` enum values used by backend domain types.
- This matrix should be updated whenever templates or required fields change.
- Judges/reviewers should verify generated sample artifacts under `docs/samples/` during demo.
