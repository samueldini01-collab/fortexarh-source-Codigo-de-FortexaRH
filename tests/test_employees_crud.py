"""
Test Employee CRUD operations with expanded model fields
Tests: Create, Read, Update, Delete employees with all new fields
Including: Datos Principales, Contrato, Descuentos, Forma de Pago, Contactos de Emergencia
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "test123"

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("token")

@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

class TestEmployeeBasicCRUD:
    """Basic Employee CRUD operations"""
    
    def test_get_employees_list(self, auth_headers):
        """Test GET /api/employees returns list"""
        response = requests.get(f"{BASE_URL}/api/employees", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"✓ GET /api/employees - Found {len(response.json())} employees")
    
    def test_create_employee_minimal(self, auth_headers):
        """Test creating employee with minimal required fields"""
        unique_id = uuid.uuid4().hex[:8]
        employee_data = {
            "first_name": f"TEST_Min_{unique_id}",
            "last_name": "Empleado",
            "email": f"test_min_{unique_id}@test.com",
            "position": "Analista",
            "department": "TI",
            "hire_date": "2024-01-15",
            "salary": 35000.00
        }
        
        response = requests.post(f"{BASE_URL}/api/employees", json=employee_data, headers=auth_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        assert "employee_id" in data
        assert "message" in data
        print(f"✓ Created minimal employee: {data['employee_id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/employees/{data['employee_id']}", headers=auth_headers)
    
    def test_create_employee_full_datos_principales(self, auth_headers):
        """Test creating employee with all Datos Principales fields"""
        unique_id = uuid.uuid4().hex[:8]
        employee_data = {
            # Datos Principales
            "first_name": f"TEST_Juan_{unique_id}",
            "last_name": "Pérez Rodriguez",
            "email": f"test_juan_{unique_id}@empresa.com",
            "phone": "809-555-1234",
            "whatsapp": "809-555-5678",
            "nationality": "Dominicana",
            "document_type": "Cédula",
            "document_number": "001-1234567-8",
            "gender": "Masculino",
            "birth_date": "1990-05-15",
            "marital_status": "Casado/a",
            "status": "active",
            "address": "Calle Principal #123, Sector Los Prados",
            "city": "Santo Domingo",
            "photo_url": "https://example.com/photo.jpg",
            # Required contract fields
            "position": "Gerente de TI",
            "department": "TI",
            "hire_date": "2024-01-15",
            "salary": 85000.00
        }
        
        response = requests.post(f"{BASE_URL}/api/employees", json=employee_data, headers=auth_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        employee_id = data['employee_id']
        
        # Verify data was saved correctly
        get_response = requests.get(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)
        assert get_response.status_code == 200
        saved = get_response.json()
        
        assert saved["first_name"] == employee_data["first_name"]
        assert saved["last_name"] == employee_data["last_name"]
        assert saved["email"] == employee_data["email"]
        assert saved["phone"] == employee_data["phone"]
        assert saved["whatsapp"] == employee_data["whatsapp"]
        assert saved["nationality"] == employee_data["nationality"]
        assert saved["document_type"] == employee_data["document_type"]
        assert saved["document_number"] == employee_data["document_number"]
        assert saved["gender"] == employee_data["gender"]
        assert saved["birth_date"] == employee_data["birth_date"]
        assert saved["marital_status"] == employee_data["marital_status"]
        assert saved["address"] == employee_data["address"]
        assert saved["city"] == employee_data["city"]
        print(f"✓ Created employee with full Datos Principales: {employee_id}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)

class TestEmployeeContractFields:
    """Test Contract (Contrato) fields"""
    
    def test_create_employee_with_contract_fields(self, auth_headers):
        """Test creating employee with all contract fields"""
        unique_id = uuid.uuid4().hex[:8]
        employee_data = {
            "first_name": f"TEST_Contract_{unique_id}",
            "last_name": "Contrato",
            "email": f"test_contract_{unique_id}@test.com",
            # Contract fields
            "position": "Desarrollador Senior",
            "department": "TI",
            "hire_date": "2024-01-15",
            "contract_type": "Indefinido",
            "contract_end_date": "",
            "salary": 75000.00,
            "supervisor": "Juan Gerente",
            "work_schedule": "Lunes a Viernes 8:00 AM - 5:00 PM",
            "exclude_from_payroll": False,
            "last_raise_date": "2024-06-01"
        }
        
        response = requests.post(f"{BASE_URL}/api/employees", json=employee_data, headers=auth_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        employee_id = response.json()['employee_id']
        
        # Verify contract fields
        get_response = requests.get(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)
        saved = get_response.json()
        
        assert saved["contract_type"] == "Indefinido"
        assert saved["supervisor"] == "Juan Gerente"
        assert saved["work_schedule"] == "Lunes a Viernes 8:00 AM - 5:00 PM"
        assert saved["exclude_from_payroll"] == False
        assert saved["last_raise_date"] == "2024-06-01"
        print(f"✓ Contract fields verified: {employee_id}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)
    
    def test_create_employee_temporal_contract(self, auth_headers):
        """Test creating employee with temporal contract"""
        unique_id = uuid.uuid4().hex[:8]
        employee_data = {
            "first_name": f"TEST_Temporal_{unique_id}",
            "last_name": "Contrato",
            "email": f"test_temporal_{unique_id}@test.com",
            "position": "Pasante",
            "department": "Marketing",
            "hire_date": "2024-06-01",
            "contract_type": "Temporal",
            "contract_end_date": "2024-12-31",
            "salary": 25000.00,
            "exclude_from_payroll": True
        }
        
        response = requests.post(f"{BASE_URL}/api/employees", json=employee_data, headers=auth_headers)
        assert response.status_code == 200
        employee_id = response.json()['employee_id']
        
        get_response = requests.get(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)
        saved = get_response.json()
        
        assert saved["contract_type"] == "Temporal"
        assert saved["contract_end_date"] == "2024-12-31"
        assert saved["exclude_from_payroll"] == True
        print(f"✓ Temporal contract verified: {employee_id}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)

class TestEmployeeDeductions:
    """Test Deductions (Descuentos) fields"""
    
    def test_create_employee_with_default_deductions(self, auth_headers):
        """Test employee has default TSS deductions enabled"""
        unique_id = uuid.uuid4().hex[:8]
        employee_data = {
            "first_name": f"TEST_Deductions_{unique_id}",
            "last_name": "Default",
            "email": f"test_ded_{unique_id}@test.com",
            "position": "Contador",
            "department": "Finanzas",
            "hire_date": "2024-01-15",
            "salary": 45000.00
        }
        
        response = requests.post(f"{BASE_URL}/api/employees", json=employee_data, headers=auth_headers)
        assert response.status_code == 200
        employee_id = response.json()['employee_id']
        
        get_response = requests.get(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)
        saved = get_response.json()
        
        # Default deductions should be True
        assert saved["afp_discount"] == True
        assert saved["sfs_discount"] == True
        assert saved["isr_discount"] == True
        print(f"✓ Default deductions verified: AFP={saved['afp_discount']}, SFS={saved['sfs_discount']}, ISR={saved['isr_discount']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)
    
    def test_create_employee_with_additional_deductions(self, auth_headers):
        """Test employee with additional deductions array"""
        unique_id = uuid.uuid4().hex[:8]
        employee_data = {
            "first_name": f"TEST_AddDed_{unique_id}",
            "last_name": "Descuentos",
            "email": f"test_addded_{unique_id}@test.com",
            "position": "Vendedor",
            "department": "Ventas",
            "hire_date": "2024-01-15",
            "salary": 40000.00,
            "additional_deductions": [
                {"type": "Préstamo Empresa", "description": "Cuota 1/10", "amount": 5000, "is_percentage": False},
                {"type": "Seguro Adicional", "description": "Seguro de vida", "amount": 2.5, "is_percentage": True}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/employees", json=employee_data, headers=auth_headers)
        assert response.status_code == 200
        employee_id = response.json()['employee_id']
        
        get_response = requests.get(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)
        saved = get_response.json()
        
        assert len(saved["additional_deductions"]) == 2
        assert saved["additional_deductions"][0]["type"] == "Préstamo Empresa"
        assert saved["additional_deductions"][0]["amount"] == 5000
        assert saved["additional_deductions"][1]["is_percentage"] == True
        print(f"✓ Additional deductions verified: {len(saved['additional_deductions'])} deductions")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)

class TestEmployeePaymentInfo:
    """Test Payment (Forma de Pago) fields"""
    
    def test_create_employee_with_bank_transfer(self, auth_headers):
        """Test employee with bank transfer payment method"""
        unique_id = uuid.uuid4().hex[:8]
        employee_data = {
            "first_name": f"TEST_Bank_{unique_id}",
            "last_name": "Transfer",
            "email": f"test_bank_{unique_id}@test.com",
            "position": "Analista",
            "department": "Finanzas",
            "hire_date": "2024-01-15",
            "salary": 55000.00,
            "payment_method": "Transferencia Bancaria",
            "payment_frequency": "Quincenal",
            "bank_name": "Banco Popular",
            "account_type": "Ahorros",
            "account_number": "123456789012"
        }
        
        response = requests.post(f"{BASE_URL}/api/employees", json=employee_data, headers=auth_headers)
        assert response.status_code == 200
        employee_id = response.json()['employee_id']
        
        get_response = requests.get(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)
        saved = get_response.json()
        
        assert saved["payment_method"] == "Transferencia Bancaria"
        assert saved["payment_frequency"] == "Quincenal"
        assert saved["bank_name"] == "Banco Popular"
        assert saved["account_type"] == "Ahorros"
        assert saved["account_number"] == "123456789012"
        print(f"✓ Bank transfer payment verified: {saved['bank_name']} - {saved['account_number']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)
    
    def test_create_employee_with_check_payment(self, auth_headers):
        """Test employee with check payment method"""
        unique_id = uuid.uuid4().hex[:8]
        employee_data = {
            "first_name": f"TEST_Check_{unique_id}",
            "last_name": "Payment",
            "email": f"test_check_{unique_id}@test.com",
            "position": "Operador",
            "department": "Operaciones",
            "hire_date": "2024-01-15",
            "salary": 30000.00,
            "payment_method": "Cheque",
            "payment_frequency": "Mensual"
        }
        
        response = requests.post(f"{BASE_URL}/api/employees", json=employee_data, headers=auth_headers)
        assert response.status_code == 200
        employee_id = response.json()['employee_id']
        
        get_response = requests.get(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)
        saved = get_response.json()
        
        assert saved["payment_method"] == "Cheque"
        assert saved["payment_frequency"] == "Mensual"
        print(f"✓ Check payment verified: {saved['payment_method']} - {saved['payment_frequency']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)

class TestEmployeeEmergencyContacts:
    """Test Emergency Contacts (Contactos de Emergencia) fields"""
    
    def test_create_employee_with_emergency_contacts(self, auth_headers):
        """Test employee with emergency contacts array"""
        unique_id = uuid.uuid4().hex[:8]
        employee_data = {
            "first_name": f"TEST_Emergency_{unique_id}",
            "last_name": "Contacts",
            "email": f"test_emerg_{unique_id}@test.com",
            "position": "Asistente",
            "department": "Administración",
            "hire_date": "2024-01-15",
            "salary": 28000.00,
            "emergency_contacts": [
                {
                    "name": "Maria Pérez",
                    "relationship": "Esposo/a",
                    "phone": "809-555-1111",
                    "whatsapp": "809-555-1111",
                    "address": "Calle 1 #10"
                },
                {
                    "name": "Carlos Rodriguez",
                    "relationship": "Padre",
                    "phone": "809-555-2222",
                    "whatsapp": "",
                    "address": ""
                }
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/employees", json=employee_data, headers=auth_headers)
        assert response.status_code == 200
        employee_id = response.json()['employee_id']
        
        get_response = requests.get(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)
        saved = get_response.json()
        
        assert len(saved["emergency_contacts"]) == 2
        assert saved["emergency_contacts"][0]["name"] == "Maria Pérez"
        assert saved["emergency_contacts"][0]["relationship"] == "Esposo/a"
        assert saved["emergency_contacts"][1]["name"] == "Carlos Rodriguez"
        print(f"✓ Emergency contacts verified: {len(saved['emergency_contacts'])} contacts")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)
    
    def test_create_employee_with_max_emergency_contacts(self, auth_headers):
        """Test employee with maximum 3 emergency contacts"""
        unique_id = uuid.uuid4().hex[:8]
        employee_data = {
            "first_name": f"TEST_MaxEmerg_{unique_id}",
            "last_name": "Contacts",
            "email": f"test_maxemerg_{unique_id}@test.com",
            "position": "Supervisor",
            "department": "Operaciones",
            "hire_date": "2024-01-15",
            "salary": 50000.00,
            "emergency_contacts": [
                {"name": "Contacto 1", "relationship": "Esposo/a", "phone": "809-111-1111"},
                {"name": "Contacto 2", "relationship": "Padre", "phone": "809-222-2222"},
                {"name": "Contacto 3", "relationship": "Madre", "phone": "809-333-3333"}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/employees", json=employee_data, headers=auth_headers)
        assert response.status_code == 200
        employee_id = response.json()['employee_id']
        
        get_response = requests.get(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)
        saved = get_response.json()
        
        assert len(saved["emergency_contacts"]) == 3
        print(f"✓ Max emergency contacts (3) verified")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)

class TestEmployeeUpdate:
    """Test Employee Update operations"""
    
    def test_update_employee_basic_info(self, auth_headers):
        """Test updating employee basic information"""
        unique_id = uuid.uuid4().hex[:8]
        # Create employee
        employee_data = {
            "first_name": f"TEST_Update_{unique_id}",
            "last_name": "Original",
            "email": f"test_update_{unique_id}@test.com",
            "position": "Junior",
            "department": "TI",
            "hire_date": "2024-01-15",
            "salary": 30000.00
        }
        
        create_response = requests.post(f"{BASE_URL}/api/employees", json=employee_data, headers=auth_headers)
        assert create_response.status_code == 200
        employee_id = create_response.json()['employee_id']
        
        # Update employee
        updated_data = {
            **employee_data,
            "first_name": f"TEST_Updated_{unique_id}",
            "last_name": "Modificado",
            "position": "Senior",
            "salary": 50000.00
        }
        
        update_response = requests.put(f"{BASE_URL}/api/employees/{employee_id}", json=updated_data, headers=auth_headers)
        assert update_response.status_code == 200
        
        # Verify update
        get_response = requests.get(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)
        saved = get_response.json()
        
        assert saved["first_name"] == f"TEST_Updated_{unique_id}"
        assert saved["last_name"] == "Modificado"
        assert saved["position"] == "Senior"
        assert saved["salary"] == 50000.00
        print(f"✓ Employee update verified: {employee_id}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)
    
    def test_update_employee_add_deductions(self, auth_headers):
        """Test updating employee to add additional deductions"""
        unique_id = uuid.uuid4().hex[:8]
        # Create employee without deductions
        employee_data = {
            "first_name": f"TEST_AddDed_{unique_id}",
            "last_name": "Update",
            "email": f"test_addded_upd_{unique_id}@test.com",
            "position": "Analista",
            "department": "Finanzas",
            "hire_date": "2024-01-15",
            "salary": 45000.00,
            "additional_deductions": []
        }
        
        create_response = requests.post(f"{BASE_URL}/api/employees", json=employee_data, headers=auth_headers)
        employee_id = create_response.json()['employee_id']
        
        # Update with deductions
        updated_data = {
            **employee_data,
            "additional_deductions": [
                {"type": "Préstamo Empresa", "description": "Préstamo personal", "amount": 3000, "is_percentage": False}
            ]
        }
        
        update_response = requests.put(f"{BASE_URL}/api/employees/{employee_id}", json=updated_data, headers=auth_headers)
        assert update_response.status_code == 200
        
        get_response = requests.get(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)
        saved = get_response.json()
        
        assert len(saved["additional_deductions"]) == 1
        assert saved["additional_deductions"][0]["amount"] == 3000
        print(f"✓ Employee deductions update verified")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)

class TestEmployeeDelete:
    """Test Employee Delete operations"""
    
    def test_delete_employee(self, auth_headers):
        """Test deleting an employee"""
        unique_id = uuid.uuid4().hex[:8]
        # Create employee
        employee_data = {
            "first_name": f"TEST_Delete_{unique_id}",
            "last_name": "ToDelete",
            "email": f"test_delete_{unique_id}@test.com",
            "position": "Temporal",
            "department": "TI",
            "hire_date": "2024-01-15",
            "salary": 25000.00
        }
        
        create_response = requests.post(f"{BASE_URL}/api/employees", json=employee_data, headers=auth_headers)
        employee_id = create_response.json()['employee_id']
        
        # Delete employee
        delete_response = requests.delete(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)
        assert delete_response.status_code == 200
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)
        assert get_response.status_code == 404
        print(f"✓ Employee deletion verified: {employee_id}")
    
    def test_delete_nonexistent_employee(self, auth_headers):
        """Test deleting non-existent employee returns 404"""
        response = requests.delete(f"{BASE_URL}/api/employees/emp_nonexistent123", headers=auth_headers)
        assert response.status_code == 404
        print("✓ Delete non-existent employee returns 404")

class TestEmployeeFullWorkflow:
    """Test complete employee workflow with all fields"""
    
    def test_full_employee_lifecycle(self, auth_headers):
        """Test complete Create -> Read -> Update -> Delete workflow"""
        unique_id = uuid.uuid4().hex[:8]
        
        # 1. CREATE with all fields
        full_employee = {
            # Datos Principales
            "first_name": f"TEST_Full_{unique_id}",
            "last_name": "Workflow Test",
            "email": f"test_full_{unique_id}@empresa.com",
            "phone": "809-555-1234",
            "whatsapp": "809-555-5678",
            "nationality": "Dominicana",
            "document_type": "Cédula",
            "document_number": "001-9999999-9",
            "gender": "Masculino",
            "birth_date": "1985-03-20",
            "marital_status": "Casado/a",
            "status": "active",
            "address": "Av. Winston Churchill #100",
            "city": "Santo Domingo",
            "photo_url": "",
            # Contrato
            "position": "Director de Tecnología",
            "department": "TI",
            "hire_date": "2020-01-15",
            "contract_type": "Indefinido",
            "contract_end_date": "",
            "salary": 150000.00,
            "supervisor": "",
            "work_schedule": "Lunes a Viernes 9:00 AM - 6:00 PM",
            "exclude_from_payroll": False,
            "last_raise_date": "2024-01-01",
            # Descuentos
            "afp_discount": True,
            "sfs_discount": True,
            "isr_discount": True,
            "additional_deductions": [
                {"type": "Seguro Adicional", "description": "Seguro de vida premium", "amount": 5000, "is_percentage": False}
            ],
            # Forma de Pago
            "payment_method": "Transferencia Bancaria",
            "payment_frequency": "Quincenal",
            "bank_name": "Banco BHD León",
            "account_type": "Corriente",
            "account_number": "9876543210",
            # Contactos de Emergencia
            "emergency_contacts": [
                {"name": "Ana García", "relationship": "Esposo/a", "phone": "809-111-2222", "whatsapp": "809-111-2222", "address": "Mismo domicilio"},
                {"name": "Pedro Workflow", "relationship": "Hermano/a", "phone": "809-333-4444", "whatsapp": "", "address": ""}
            ]
        }
        
        create_response = requests.post(f"{BASE_URL}/api/employees", json=full_employee, headers=auth_headers)
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        employee_id = create_response.json()['employee_id']
        print(f"✓ Step 1: Created full employee: {employee_id}")
        
        # 2. READ and verify all fields
        get_response = requests.get(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)
        assert get_response.status_code == 200
        saved = get_response.json()
        
        # Verify key fields
        assert saved["first_name"] == full_employee["first_name"]
        assert saved["salary"] == 150000.00
        assert saved["contract_type"] == "Indefinido"
        assert saved["payment_method"] == "Transferencia Bancaria"
        assert len(saved["additional_deductions"]) == 1
        assert len(saved["emergency_contacts"]) == 2
        print(f"✓ Step 2: Read and verified all fields")
        
        # 3. UPDATE - change position and salary
        updated_employee = {
            **full_employee,
            "position": "CTO",
            "salary": 180000.00,
            "last_raise_date": "2024-12-01"
        }
        
        update_response = requests.put(f"{BASE_URL}/api/employees/{employee_id}", json=updated_employee, headers=auth_headers)
        assert update_response.status_code == 200
        
        # Verify update
        get_updated = requests.get(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)
        updated = get_updated.json()
        assert updated["position"] == "CTO"
        assert updated["salary"] == 180000.00
        print(f"✓ Step 3: Updated employee - new position: CTO, new salary: 180000")
        
        # 4. DELETE
        delete_response = requests.delete(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)
        assert delete_response.status_code == 200
        
        # Verify deletion
        get_deleted = requests.get(f"{BASE_URL}/api/employees/{employee_id}", headers=auth_headers)
        assert get_deleted.status_code == 404
        print(f"✓ Step 4: Deleted employee and verified 404")
        
        print(f"\n✓ FULL LIFECYCLE TEST PASSED")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
