# Trade service

A microservice designed for managing various trade-related functionalities such as documents metadata, investor types,
issuers, documents types, and transaction types. This service also integrates a database utility package for common
database utilities and logging configurations. It leverages databases such as MySQL Server and ensures configurations
are set correctly via .env file.

## Getting Started

- To use the dbutil_common utilities, ensure you use `git submodule update --init --recursive` to get dbutil files (\n
  common.py)

## Prerequisites

- Python 3.x
- MySQL Server (Version 8.0 recommended)
- Logging configuration setup (via logger_config.py)

## Changelog

### v0.0.1

- Initial
- Added /lookup_app_rules/{app_id}
- Added /look_app_rule_by_id/{app_id,rule_id}
- Added "/update_app_rule/" - Use PASS or FAIL for Status

* Pending fix from SP to return override in look_app_rule_by_id *

### v0.0.2

- Added requirements.txt
- Synced with db v1.0.30

### v0.0.3

- Synced with db v1.0.39
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

### v0.0.4

- Fixed db_trade/handle_sp_call for empty list message
- Fixed return message, handler error /update_app_rule
- Synced with db v1.0.40

### v0.0.5

- Added /list_all_transaction_types return all transaction types
- Added /list_all_trades return trade records
- Synced with db v1.0.42

### v0.0.6

- Integration of dbutil_package submodule; utilization of common database utilities and logging configurations.

### v0.0.7 (latest)

- Update dbutil to v0.0.5: Enhanced `DatabaseHandler` with environment variable management for database configuration.

## Configuration

Ensure your `.env` file is properly configured with `DATABASE_URL`, `DATABASE_PASSWORD` and other necessary settings for
your MySQL database connection.

- `DATABASE_URL=mysql://<username>@<host>:<port>/<database_name>`
- `DATABASE_PASSWORD=<database_password>`