import logging
from datetime import datetime, date
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError, Json
from typing import Any, Dict, List, Union
from dbutil_package.db_trades import AppRulesDataRetriever
from logger_config import setup_logging
import json
from enum import Enum,IntEnum

# Initialize logging.
setup_logging()
class RuleStatusEnum(Enum):
    PASS = 1
    FAIL = 2
    
class ApplicationRuleUpdateModel(BaseModel):
    id: int
    applicationId: int
    ruleId: int
    override: bool
    status: str
    notes: str

# # Function to handle datetime and date object serialization.
# def _json_serial(obj):
#     if isinstance(obj, (datetime, date)):
#         return obj.isoformat()
#     raise TypeError("Type %s not serializable" % type(obj))

# def is_admin(request: Request):
#     role = request.headers.get('role', None)
#     if role != "admin":
#         raise HTTPException(status_code=403, detail="Not enough permissions")
#     return role

app = FastAPI()

# Set CORS to allow all origins.
origins = ["*"]

# Initialize RepDataRetriever to interact with DB
data_retriever = AppRulesDataRetriever()

class DatabaseError(Exception):
    pass

# Add CORS middleware settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS", "POST", "DELETE"], 
    allow_headers=["*"],  # Can be customized to allow specific headers.
)

# Helper function to handle errors
def handle_error(e: Exception, message: str):
    logging.error(f"{message}: {e}")
    return {"error": message}, 500

# # Checks if a given date is the last day of the year
# def is_last_day_of_year(target_date: datetime.date) -> bool:
#     last_day_of_year = datetime(target_date.year, 12, 31).date()
#     return target_date == last_day_of_year

# Making fields required by default in Pydantic model

@app.get("/lookup_app_rules/{app_id}", status_code=200)
async def lookup_app_rules(app_id: int):
    result = data_retriever.lookup_app_rules(app_id)
    
    if result.get("status") == "error":
        if result.get("error_code") == "DB_ERR":
            return {"status": "error", "message": "Database Error: Sales rep does not exist"}
    
    if result.get("status") == "success" and result.get("data") is None:
        logging.error(f"Failed to lookup application rules {app_id}")
        return result 
    
    if result.get("status") == "success":
        logging.info(f"Successfully retrieved rules for application  {app_id}")  
        return result
    
    logging.error(f"Failed to lookup rules for application {app_id}")
    return {"status":"error", "message" :f"Failed to lookup rules for application {app_id}. ID not found."}

@app.get("/look_app_rule_by_id/{app_id,rule_id}", status_code=200)
async def look_app_rule_by_id(app_id: int, rule_id: int):
    result = data_retriever.look_app_rule_by_id(app_id, rule_id)
    if result.get("status") == "error":
        if result.get("error_code") == "DB_ERR":
            return {"status": "error", "message": "Database Error: Application Rule does not exist"}
    
    if result.get("status") == "success" and result.get("data") is None:
        logging.error(f"Failed to lookup rule {rule_id} for application {app_id}")
        return result 
    
    if result.get("status") == "success":
        logging.info(f"Successfully retrieved rule {rule_id} for application  {app_id}")  
        return result
    
    logging.error(f"Failed to lookup rule {rule_id} for application {app_id}")
    return {"status":"error", "message" :f"Failed to lookup rule {rule_id} for application {app_id}. ID not found."}

@app.post("/update_app_rule/")
async def update_app_ruke(app_rule_data: ApplicationRuleUpdateModel):
    try:
        # Remove created_by from the model if it exists
        app_rule_data_dict = app_rule_data.model_dump()
        app_rule_data_dict.pop('created_by', None)
    
        # Hardcode 'created_by' as 'user' before calling stored procedure
        app_rule_data_dict['user'] = 'user'
    
        # check if status is PASS or FaiL
        if app_rule_data_dict['status'] not in ['PASS','FAIL']:
            logging.error(f"Application Rule Status must be PASS or FAIL: {app_rule_data_dict['status']}")
            return {"status":"error", "message" :f"Application Rule Status must be PASS or FAIL: {app_rule_data_dict['status']}"}
        
        result = data_retriever.update_app_rule(app_rule_data_dict) 
        
        if result.get('status') == 'error':
            logging.error(f"Error while updating app rule: {result['message']}")
            return result
        
        logging.info("Successfully updated app rule.")
        return result

    except HTTPException as e:  # Catching FastAPI's HTTPException
        raise

    except Exception as e:
        logging.error(f"Unexpected error while updating app rule: {e}")
        return {"status":"error", "message": f"Unexpected error while updating app rule: {str(e)}" }
    
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)