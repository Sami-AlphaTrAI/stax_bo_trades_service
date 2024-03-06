from mysql.connector import Error
from datetime import date, datetime
import logging
import logger_config
import mysql.connector
from fastapi import HTTPException
import json
import os


# Custom Exceptions
class DatabaseError(Exception):
    pass


class UpsertException(Exception):
    pass


class RepNotFoundError(Exception):
    pass


class DBHandler:
    def __init__(self, connection):
        self.conn = connection

    def handle_sp_call(self, sp, params=None, rec_type_key=None, msg_only=False, rec_type_in_data=False) -> dict:
        try:
            data = self._execute_sp(sp, params)
            data_result = {}
            # Initialize the response dictionary
            response = {}
            message = ""

            if msg_only:
                if len(data) is not 0:
                    message = list(data[0].keys())[0]

                response["message"] = message

                self.conn.commit()
                response["status"] = "success"
                return response

            if rec_type_key is not None and len(data) > 0 and len(list(data[0].keys())) > 1:
                data_result[rec_type_key] = data
                response["data"] = data_result
                self.conn.commit()
                response["status"] = "success"
                return response

            if rec_type_key is not None and len(data) > 0 and len(list(data[0].keys())) == 1:
                response["status"] = "error"
                response["message"] = list(data[0].keys())[0]
                self.conn.commit()
                return response

            if rec_type_key is not None and len(data) == 0:
                response["status"] = "success"
                data_result = data
                response["data"] = data_result
                self.conn.commit()
                return response

            if rec_type_key is not None and data_rec.get(rec_type_key) is None:
                response["status"] = "error"
                response["message"] = list(data[0].keys())[0]
                self.conn.commit()
                return response

            if rec_type_in_data:
                for data_rec in data:
                    # if we are expecting rec_type_in data and we did not get one
                    # then it must have been an error
                    if data_rec.get("rec_type") is None:
                        response["status"] = "error"
                        response["message"] = list(data[0].keys())[0]
                        self.conn.commit()
                        return response
                    if data_rec.get("rec_type") is not None:
                        rec_type = data_rec.pop('rec_type')
                        data_result.setdefault(rec_type, []).append(data_rec)
                if data_result:
                    response["data"] = data_result
                    self.conn.commit()
                    if response.get("status") is None:  # check if we have already set the status
                        response["status"] = "success"

                        # If there's any processed data, add it to the response
            # if data_result:
            #    response["data"] = data_result   
            # self.conn.commit()
            # if response.get("status") is None: # check if we have already set the status
            #    response["status"] = "success"
            return response

        # Handle any database related errors
        except mysql.connector.Error as e:
            self.conn.rollback()
            logging.error(f"Database Error: {e}")
            return {"status": "error", "message": f"Database error: {str(e)}"}

        # Handle all other exceptions
        except Exception as e:
            logging.error(f"Unexpected Error: {e}")
            return {"status": "error", "message": f"Unexpected error: {str(e)}"}

    def _execute_sp(self, sp, params=[]):
        data = []
        cursor = self.conn.cursor()

        try:
            if params:
                cursor.callproc(sp, params)
            else:
                cursor.callproc(sp)

            results = cursor.stored_results()

            for result in results:
                rows = result.fetchall()

                if rows:
                    columns = [column[0] for column in result.description]
                    for row in rows:
                        data.append(dict(zip(columns, row)))

            return data

        finally:  # To ensure the cursor always gets closed.
            if cursor:
                cursor.close()


class AppRulesDataRetriever:
    class DeleteRepError(Exception):
        pass

    def __init__(self):
        """
        Creates a connection to a MySQL database using environment variables,
        or falls back to a local connection if environment variables are not set.
        """
        # Attempt to use environment variables for the connection
        host = os.environ.get('MYSQL_HOST', 'localhost')
        user = os.environ.get('MYSQL_USER', 'root')
        password = os.environ.get('MYSQL_PASSWORD', 'Password')
        database = os.environ.get('MYSQL_DATABASE', 'stax_backoffice')
        self.db_config = {
            "host": host,
            "user": user,
            "password": password,
            "database": database,
        }
        logger_config.setup_logging()
        try:
            connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )

            self.conn = self.create_connection()
            self.db_handler = DBHandler(self.conn)

        except Error as e:
            logging.error("DB Error: %s", str(e))
            # return {"error": f"Database error: {e}"}

    # Establish a new database connection
    def create_connection(self):
        try:
            conn = mysql.connector.connect(**self.db_config)
            if conn.is_connected():
                logging.info('Successfully connected to MySQL database')
            return conn
        except Error as e:
            logging.error(f"Error connecting to MySQL: {e}")
            raise HTTPException(status_code=500, detail="Database connection error")

    # Serializes datetime and date objects for JSON
    def _json_serial(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError("Type %s not serializable" % type(obj))

    # Retrieve specific app rules statuses
    def lookup_app_rules(self, a_app_id: int) -> dict:
        return self.db_handler.handle_sp_call("sp_reg_review_lookup_AppId", [a_app_id], rec_type_key="app_rules_list")

    # Retrieve sepecific rule for specific app
    def look_app_rule_by_id(self, app_id, rule_id):
        return self.db_handler.handle_sp_call("sp_reg_review_lookup_RuleId", [app_id, rule_id], rec_type_key="app_rule")

    # update rule status for specific app
    def update_app_rule(self, app_rule_data: dict) -> dict:
        params = [
            app_rule_data['id'],
            app_rule_data['applicationId'],
            app_rule_data['ruleId'],
            app_rule_data['override'],
            app_rule_data['status'],
            app_rule_data['notes'],
            app_rule_data['user']
        ]
        return self.db_handler.handle_sp_call("sp_reg_rule_review_update", params, msg_only=True)

    # create trade doc meta 
    def create_trade_documents_meta(self, trade_doc_meta: dict):
        params = [trade_doc_meta.get(key) for key in
                  ['td_id', 'issuer_id', 'investor_type', 'document_type_id', 'optional', 'email_address', 'notes',
                   'created_by']]
        return self.db_handler.handle_sp_call("sp_trade_documents_meta_create", params, msg_only=True)

    # update trade doc meta 
    def update_trade_documents_meta(self, trade_doc_meta: dict):
        params = [trade_doc_meta.get(key) for key in
                  ['td_id', 'issuer_id', 'investor_type', 'document_type_id', 'optional', 'email_address', 'notes',
                   'created_by']]
        return self.db_handler.handle_sp_call("sp_trade_documents_meta_update", params, msg_only=True)

    # delete trade doc meta
    def delete_trade_documents_meta(self, trade_doc_meta: dict):
        params = [trade_doc_meta.get(key) for key in
                  ['td_id', 'created_by']]
        return self.db_handler.handle_sp_call("sp_trade_documents_meta_delete", params, msg_only=True)

    # list trade documents meta 
    def list_trade_docs_meta(self):
        return self.db_handler.handle_sp_call("sp_trade_documents_meta_list", rec_type_key="TRADE_DOCUMENTS_META")

    # create investor type
    def create_investor_type(self, investor_type: dict):
        params = [investor_type.get(key) for key in ['investor_id', 'name', 'description', 'created_by']]
        return self.db_handler.handle_sp_call("sp_investor_type_create", params, msg_only=True)

    # update investor type 
    def update_investor_type(self, investor_type: dict):
        params = [investor_type.get(key) for key in ['investor_id', 'name', 'description', 'created_by']]
        return self.db_handler.handle_sp_call("sp_investor_type_update", params, msg_only=True)

    # delete investor type 
    def delete_investor_type(self, investor_type: dict):
        params = [investor_type.get(key) for key in ['investor_id', 'created_by']]
        return self.db_handler.handle_sp_call("sp_investor_type_delete", params, msg_only=True)

    # list investor type 
    def list_all_investor_type(self):
        return self.db_handler.handle_sp_call("sp_investor_type_list", rec_type_key='INVESTOR_TYPE_LIST')

    # list_issuers_list
    def list_issuers_list(self):
        return self.db_handler.handle_sp_call("sp_trade_issuers_list", rec_type_key="ISSUERS_LIST")

    # list_document_type
    def lookup_list_document_type_by_name(self, name: str):
        params = [name]
        return self.db_handler.handle_sp_call("sp_lookup_doctypes_name", params, rec_type_key="DOC_TYPE")

    # list_document_type
    def lookup_list_document_type_by_id(self, id: int):
        params = [id]
        return self.db_handler.handle_sp_call("sp_lookup_doctypes_id", params, rec_type_key="DOC_TYPE")
