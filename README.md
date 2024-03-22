+ v0.0.6
    + integration of dbutil_package submodule; utilization of common database utilities and logging configurations.


+ v0.0.5
    + adding /list_all_transaction_types return all transaction types
    + adding /list_all_trades return trade records
    + tested with db v1.0.42


+ v0.0.4
    + tested with db v1.0.40
    + fix db_trade/handle_sp_call for empty list message
    + fix return message, handler error /update_app_rule


+ v0.0.3
    - tested with db v1.0.39
    - Added /create_trade_doc_meta
    - Added /update_trade_doc_meta
    - Added /delete_trade_doc_meta
    - Added /list_trade_docs_meta
    - Added /create_investor_type
    - Added /update_investor_type
    - Added /delete_investor_type
    - Added /list_investor_type
    - Added /list_issuers_list
    - Added /list_document_type_name/{type_name}
    - Added /list_document_type_id/{type_id}


+ v0.0.2
    - added requirements.txt
    - tested with db v1.0.30

+ v0.0.1
    - Initial
    - Added /lookup_app_rules/{app_id}
    - Added /look_app_rule_by_id/{app_id,rule_id}
    - Added "/update_app_rule/" - Use PASS or FAIL for Status

    * Pending fix from SP to return override in look_app_rule_by_id *
