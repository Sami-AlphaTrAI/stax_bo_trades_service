from dbutil_package.dbutil.common import DatabaseHandler


class AppRulesDataRetriever(DatabaseHandler):
    class DeleteRepError(Exception):
        pass

    def __init__(self):
        super().__init__()
        self.db_handler = self.trades_handle_sp_call(self.conn)
        # def __init__(self):
        #     """
        #     Creates a connection to a MySQL database using environment variables,
        #     or falls back to a local connection if environment variables are not set.
        #     """
        #     # Attempt to use environment variables for the connection
        #     host = os.environ.get('MYSQL_HOST', 'localhost')
        #     user = os.environ.get('MYSQL_USER', 'root')
        #     password = os.environ.get('MYSQL_PASSWORD', 'Password')
        #     database = os.environ.get('MYSQL_DATABASE', 'stax_backoffice')
        #     self.db_config = {
        #         "host": host,
        #         "user": user,
        #         "password": password,
        #         "database": database,
        #     }
        #     logger_config.setup_logging()
        #     try:
        #         connection = mysql.connector.connect(
        #             host=host,
        #             user=user,
        #             password=password,
        #             database=database
        #         )
        #
        #         self.conn = self.create_connection()
        #         self.db_handler = TradeDBHandler(self.conn)
        #
        #     except Error as e:
        #         logging.error("DB Error: %s", str(e))
        #         # return {"error": f"Database error: {e}"}
        #
        # # Establish a new database connection
        # def create_connection(self):
        #     try:
        #         conn = mysql.connector.connect(**self.db_config)
        #         if conn.is_connected():
        #             logging.info('Successfully connected to MySQL database')
        #         return conn
        #     except Error as e:
        #         logging.error(f"Error connecting to MySQL: {e}")
        #         raise HTTPException(status_code=500, detail="Database connection error")
        #
        # # Serializes datetime and date objects for JSON
        # def _json_serial(self, obj):
        #     if isinstance(obj, (datetime, date)):
        #         return obj.isoformat()
        #     raise TypeError("Type %s not serializable" % type(obj))

    # Retrieve specific app rules statuses
    def lookup_app_rules(self, a_app_id: int) -> dict:
        return self.trades_handle_sp_call("sp_reg_review_lookup_AppId", [a_app_id], rec_type_key="app_rules_list")

    # Retrieve specific rule for specific app
    def look_app_rule_by_id(self, app_id, rule_id):
        return self.trades_handle_sp_call("sp_reg_review_lookup_RuleId", [app_id, rule_id], rec_type_key="app_rule")

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
        return self.trades_handle_sp_call("sp_reg_rule_review_update", params, msg_only=True)

    def create_trade_documents_meta(self, trade_doc_meta: dict):
        params = [trade_doc_meta.get(key) for key in
                  ['td_id', 'issuer_id', 'investor_type', 'document_type_id', 'optional', 'email_address', 'notes',
                   'created_by']]
        return self.trades_handle_sp_call("sp_trade_documents_meta_create", params, msg_only=True)

    def update_trade_documents_meta(self, trade_doc_meta: dict):
        params = [trade_doc_meta.get(key) for key in
                  ['td_id', 'issuer_id', 'investor_type', 'document_type_id', 'optional', 'email_address', 'notes',
                   'created_by']]
        return self.trades_handle_sp_call("sp_trade_documents_meta_update", params, msg_only=True)

    def delete_trade_documents_meta(self, trade_doc_meta: dict):
        params = [trade_doc_meta.get(key) for key in
                  ['td_id', 'created_by']]
        return self.trades_handle_sp_call("sp_trade_documents_meta_delete", params, msg_only=True)

    def list_trade_docs_meta(self) -> dict:
        return self.trades_handle_sp_call("sp_trade_documents_meta_list", rec_type_key="TRADE_DOCUMENTS_META")

    def create_investor_type(self, investor_type: dict):
        params = [investor_type.get(key) for key in ['investor_id', 'name', 'description', 'created_by']]
        return self.trades_handle_sp_call("sp_investor_type_create", params, msg_only=True)

    def update_investor_type(self, investor_type: dict):
        params = [investor_type.get(key) for key in ['investor_id', 'name', 'description', 'created_by']]
        return self.trades_handle_sp_call("sp_investor_type_update", params, msg_only=True)

    def delete_investor_type(self, investor_type: dict):
        params = [investor_type.get(key) for key in ['investor_id', 'created_by']]
        return self.trades_handle_sp_call("sp_investor_type_delete", params, msg_only=True)

    def list_all_investor_type(self) -> dict:
        return self.trades_handle_sp_call("sp_investor_type_list", rec_type_key='INVESTOR_TYPE_LIST')

    def list_issuers_list(self) -> dict:
        return self.trades_handle_sp_call("sp_trade_issuers_list", rec_type_key="ISSUERS_LIST")

    def lookup_list_document_type_by_name(self, name: str) -> dict:
        params = [name]
        return self.trades_handle_sp_call("sp_lookup_doctypes_name", params, rec_type_key="DOC_TYPE")

    def lookup_list_document_type_by_id(self, id: int) -> dict:
        params = [id]
        return self.trades_handle_sp_call("sp_lookup_doctypes_id", params, rec_type_key="DOC_TYPE")

    def get_all_transaction_type(self) -> dict:
        return self.trades_handle_sp_call("sp_get_all_transaction_types", rec_type_key="transaction_type")

    def get_all_trade_list(self) -> dict:
        return self.trades_handle_sp_call("sp_trade_list_all", rec_type_key="TRADE_LIST")
