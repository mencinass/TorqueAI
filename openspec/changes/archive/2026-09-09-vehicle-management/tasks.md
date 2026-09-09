## 1. Domain Models & Schemas

- [x] 1.1 Create SQLAlchemy 2.0 ORM models for Brand, Model, Generation, Engine, and Vehicle in `backend/app/models/vehicle.py`
- [x] 1.2 Create SQLAlchemy 2.0 ORM model for TechnicalDocument in `backend/app/models/document.py`
- [x] 1.3 Create Pydantic v2 schemas for Vehicle and Document entities in `backend/app/schemas/`

## 2. Services & Seeding

- [x] 2.1 Implement async VehicleService for querying and persisting vehicles and components in `backend/app/services/vehicle_service.py`
- [x] 2.2 Implement async DocumentService for document metadata registration and filtering in `backend/app/services/document_service.py`
- [x] 2.3 Implement idempotent database seeder for MINI R56, MINI R53, and Fiat 500 in `backend/app/database/seed.py`

## 3. REST API Endpoints

- [x] 3.1 Implement vehicles router in `backend/app/api/v1/endpoints/vehicles.py`
- [x] 3.2 Implement documents router in `backend/app/api/v1/endpoints/documents.py`
- [x] 3.3 Register routers in `backend/app/api/v1/api.py` and hook lifespan initialization in `backend/app/main.py`

## 4. Verification & Testing

- [x] 4.1 Implement automated tests for vehicle APIs in `backend/tests/test_vehicles.py`
- [x] 4.2 Implement automated tests for document APIs in `backend/tests/test_documents.py`
- [x] 4.3 Validate and archive OpenSpec change `vehicle-management`
