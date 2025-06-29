"""
Customer management API routes.
Provides CRUD operations for customer data.
"""

from typing import List
from fastapi import APIRouter, HTTPException, Query
from google.cloud.firestore_v1.base_query import FieldFilter

from ..models import Customer, CustomerCreate, CustomerUpdate, APIResponse
from ..database import get_customers_collection

router = APIRouter()

@router.get("/", response_model=List[Customer])
async def list_customers(
    limit: int = Query(100, description="Maximum number of customers to return"),
    offset: int = Query(0, description="Number of customers to skip")
):
    """
    Retrieve a list of all customers with pagination.
    """
    try:
        customers_ref = get_customers_collection()
        
        # Apply pagination
        query = customers_ref.limit(limit).offset(offset)
        docs = query.stream()
        
        customers = []
        for doc in docs:
            try:
                customer_data = doc.to_dict()
                customer_data['id'] = doc.id
                
                # Skip invalid customers (e.g., empty names) to maintain data integrity
                if not customer_data.get('name') or not customer_data.get('phone'):
                    continue
                    
                customers.append(Customer(**customer_data))
            except Exception as validation_error:
                # Log the error but continue processing other customers
                print(f"Skipping invalid customer {doc.id}: {validation_error}")
                continue
        
        return customers
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving customers: {str(e)}")

@router.post("/", response_model=Customer)
async def create_customer(customer: CustomerCreate):
    """
    Create a new customer.
    """
    try:
        customers_ref = get_customers_collection()
        
        # Convert to dict and add to Firestore
        customer_data = customer.model_dump()
        doc_ref = customers_ref.add(customer_data)[1]
        
        # Return the created customer with ID
        customer_data['id'] = doc_ref.id
        return Customer(**customer_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating customer: {str(e)}")

@router.get("/{customer_id}", response_model=Customer)
async def get_customer(customer_id: str):
    """
    Retrieve a specific customer by ID.
    """
    try:
        customers_ref = get_customers_collection()
        doc = customers_ref.document(customer_id).get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        customer_data = doc.to_dict()
        customer_data['id'] = doc.id
        return Customer(**customer_data)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving customer: {str(e)}")

@router.put("/{customer_id}", response_model=Customer)
async def update_customer(customer_id: str, customer_update: CustomerUpdate):
    """
    Update an existing customer.
    """
    try:
        customers_ref = get_customers_collection()
        doc_ref = customers_ref.document(customer_id)
        
        # Check if customer exists
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Update only provided fields
        update_data = customer_update.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields provided for update")
        
        doc_ref.update(update_data)
        
        # Return updated customer
        updated_doc = doc_ref.get()
        customer_data = updated_doc.to_dict()
        customer_data['id'] = updated_doc.id
        return Customer(**customer_data)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating customer: {str(e)}")

@router.delete("/{customer_id}", response_model=APIResponse)
async def delete_customer(customer_id: str):
    """
    Delete a customer and all associated messages.
    """
    try:
        customers_ref = get_customers_collection()
        doc_ref = customers_ref.document(customer_id)
        
        # Check if customer exists
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Delete customer
        doc_ref.delete()
        
        # TODO: Also delete associated messages
        # This would require a batch operation or cloud function
        
        return APIResponse(
            success=True,
            message=f"Customer {customer_id} deleted successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting customer: {str(e)}")

@router.get("/search/phone", response_model=Customer)
async def find_customer_by_phone(phone: str = Query(..., description="Phone number to search for")):
    """
    Find a customer by phone number.
    """
    try:
        customers_ref = get_customers_collection()
        
        # Query by phone number
        query = customers_ref.where(filter=FieldFilter("phone", "==", phone))
        docs = list(query.stream())
        
        if not docs:
            raise HTTPException(status_code=404, detail="Customer not found with this phone number")
        
        # Return the first match
        doc = docs[0]
        customer_data = doc.to_dict()
        customer_data['id'] = doc.id
        return Customer(**customer_data)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching for customer: {str(e)}")
