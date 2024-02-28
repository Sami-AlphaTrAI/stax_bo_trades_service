import logging
from datetime import datetime, date
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError, Json
from typing import Any, Dict, List, Union
from dbutil_package.db_trades import AppRulesDataRetriever
from logger_config import setup_logging
import json
from enum import Enum, IntEnum

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


class InvestorTypeModel(BaseModel):
    name: str
    description: str
    # investorId: int
    # created_by: str


class OptionalEnum(int, Enum):
    true = 0
    false = 1


class WithdrawalDepositEnum(str, Enum):
    withdrawal = '0'
    deposit = '1'


class TradeDocMetaModel(BaseModel):
    td_id: int
    issuer_id: int
    investor_type: int
    document_type_id: int
    optional: OptionalEnum
    email_address: str
    notes: str
    created_by: str


class TransactionCreateModel(BaseModel):
    trans_acc_no: int
    trade_id: int
    posting_date: date
    trans_description: str
    withdrawal_deposit: WithdrawalDepositEnum
    trans_type_id: int
    amount: int
    created_by: str


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


def format_db_error(message: str):
    message = message.split(": ")
    if len(message) > 1:
        message = message[-1].strip().lower()
    return message


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
    return {"status": "error", "message": f"Failed to lookup rules for application {app_id}. ID not found."}


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
    return {"status": "error", "message": f"Failed to lookup rule {rule_id} for application {app_id}. ID not found."}


@app.post("/update_app_rule/")
async def update_app_rule(app_rule_data: ApplicationRuleUpdateModel):
    try:
        # Remove created_by from the model if it exists
        app_rule_data_dict = app_rule_data.model_dump()
        app_rule_data_dict.pop('created_by', None)

        # Hardcode 'created_by' as 'user' before calling stored procedure
        app_rule_data_dict['user'] = 'user'

        # check if status is PASS or FaiL
        if app_rule_data_dict['status'] not in ['PASS', 'FAIL']:
            logging.error(f"Application Rule Status must be PASS or FAIL: {app_rule_data_dict['status']}")
            return {"status": "error",
                    "message": f"Application Rule Status must be PASS or FAIL: {app_rule_data_dict['status']}"}

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
        return {"status": "error", "message": f"Unexpected error while updating app rule: {str(e)}"}


# Create trade doc meta
@app.post("/create_trade_doc_meta")
async def create_trade_doc_meta(trade_doc_meta: TradeDocMetaModel):
    try:
        trade_doc_meta_dict = trade_doc_meta.model_dump()
        trade_doc_meta_dict['optional'] = trade_doc_meta_dict['optional'].value
        result = data_retriever.create_trade_documents_meta(trade_doc_meta_dict)

        if result.get('status') == 'error' and '45000' in result['message']:
            result["message"] = "Failed to create trade documents meta"
            return result

        if result["status"] == "success" and result["message"] == "message":
            result["message"] = "successfully create trade document meta"

        logging.info("successfully create trade meta document")
        return result

    except Exception as e:
        logging.exception(f"Failed to create trade documents meta {e}")
        return {"status": "error", "message": f"Failed to create trade documents meta"}


# Update trade doc meta
@app.post("/update_trade_doc_meta")
async def update_trade_doc_meta(trade_doc_meta: TradeDocMetaModel):
    try:
        trade_doc_meta_dict = trade_doc_meta.model_dump()
        trade_doc_meta_dict['optional'] = trade_doc_meta_dict['optional'].value
        result = data_retriever.update_trade_documents_meta(trade_doc_meta_dict)

        if result["status"] == "success" and result["message"] == "message":
            result["message"] = "successfully update trade document meta "
        logging.info("update trade meta document")

        return result

    except Exception as e:
        logging.exception(f"Failed to update trade documents meta {e}")
        return {"status": "error", "message": f"Failed to update trade documents meta"}


# Delete trade doc meta
@app.delete("/delete_trade_doc_meta")
async def delete_trade_doc_meta(trade_id: int):
    try:
        trade_doc_meta_dict = {"td_id": trade_id, "create_by": "Admin"}
        result = data_retriever.delete_trade_documents_meta(trade_doc_meta_dict)

        if result.get('status') == 'error' and '45000' in result['message']:
            result["message"] = 'Trade document meta does not exist'
            return result

        if result["status"] == "success" and result["message"] == "message":
            result["message"] = "Successfully delete trade meta document"

        logging.info("Successfully delete trade meta document")

        return result

    except Exception as e:
        logging.exception(f"Failed to delete trade meta document {e}")
        return {"status": "error", "message": f"Failed to delete trade meta document"}


# List trade doc meta
@app.get("/list_trade_docs_meta")
async def list_trade_docs_meta():
    try:
        result = data_retriever.list_trade_docs_meta()
        if result['status'] == 'success':
            logging.info("Successfully retrieved list trade document meta")
        return result

    except Exception as e:
        logging.error(f"Failed to retrieve trade documents meta {e}")
        return {"status": "error", "message": "Failed to retrieve trade documents meta"}


# Create investor type
@app.post("/create_investor_type")
async def create_investor_type(investor_type: InvestorTypeModel):
    try:
        investor_type_dict = investor_type.model_dump()
        # hardcode investor_id and created_by
        investor_type_dict['created_by'] = "Admin"
        investor_type_dict['investor_id'] = 1007

        result = data_retriever.create_investor_type(investor_type_dict)

        if result['status'] == 'success' and result['message'] == 'message':
            result['message'] = "Successfully create investor type"

        logging.info(result["message"])
        return result

    except Exception as e:
        logging.exception(f"Failed to create investor type {e}")
        return {"status": "error", "message": f"Failed to create investor type"}


# Update investor type
@app.post("/update_investor_type")
async def update_investor_type(investor_type: InvestorTypeModel):
    try:
        investor_type_dict = investor_type.model_dump()

        # Hardcode investor_id and created_by
        investor_type_dict['created_by'] = "Admin"
        investor_type_dict['investor_id'] = 1007

        result = data_retriever.update_investor_type(investor_type_dict)

        if result['status'] == 'success' and result['message'] == 'message':
            result['message'] = "Successfully update investor type"

        logging.info(result["message"])
        return result

    except Exception as e:

        logging.exception(f"Failed to update investor type {e}")
        return {"status": "error", "message": f"Failed to update investor type"}


# Delete investor type
@app.delete("/delete_investor_type")
async def delete_investor_type(investor_id: int):
    try:
        # hardcode created_by
        investor_type_dict = {"investor_id": investor_id, "created_by": "Admin"}

        result = data_retriever.delete_investor_type(investor_type_dict)

        if result['status'] == 'success' and result['message'] == 'message':
            result['message'] = "Successfully investor type deleted"

        logging.info(result["message"])
        return result

    except Exception as e:
        logging.exception(f"failed to delete investor_type {e}")
        return {"status": "error", "message": f"failed to delete investor_type"}


# List investor type
@app.get("/list_investor_type")
async def list_investor_type():
    try:
        result = data_retriever.list_all_investor_type()
        logging.info("successfully list all investor type")
        return result

    except Exception as e:
        logging.error(f"failed to retrieve List all investor type {e}")
        return {"status": "error", "message": f"failed to retrieve all List all investor type"}


# list issuers type
@app.get("/list_issuers_list")
async def list_issuers_list():
    try:
        result = data_retriever.list_issuers_list()
        logging.info("Successfully list all issuers")
        return result

    except Exception as e:
        logging.error(f"Failed to retrieve list issuers type {e}")
        return {"status": "error", "message": f"Failed to retrieve list issuers type"}


# List documents type by name
@app.get("/list_document_type_name/{type_name}")
async def list_document_type_by_name(type_name: str):
    try:
        result = data_retriever.lookup_list_document_type_by_name(type_name)
        logging.info(f"Successfully list all docs type by type_name")
        return result

    except Exception as e:
        logging.error(f"Failed to retrieve List docs type with error: {e}")
        return {"status": "error", "message": f"Failed to retrieve list all docs type"}


# List documents type by name
@app.get("/list_document_type_id/{type_id}")
async def list_document_type_by_name(type_id: int):
    try:
        result = data_retriever.lookup_list_document_type_by_id(type_id)
        logging.info(f" Successfully list all list docs")
        return result

    except Exception as e:
        logging.error(f"Failed to retrieve List docs type {e}")
        return {"status": "error", "message": f"Failed to retrieve list all docs type"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8004)
