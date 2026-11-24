# Apex standards checklist

| Area | Standard |
|---|---|
| Sharing | Services `with sharing`; `without sharing` only with a documented reason |
| Security | SOQL `WITH USER_MODE`; DML `AccessLevel.USER_MODE` or `Security.stripInaccessible` |
| Bulkification | No SOQL/DML in loops; collections + maps; handle 200+ records |
| Triggers | One trigger per object, logic in a handler class, recursion guard |
| Async | Queueable for chaining/callouts; Batch for large volumes; avoid nested `@future` |
| Errors | No empty catch; LWC-facing methods throw `AuraHandledException`; log to a shared log object |
| Config | No hard-coded IDs/URLs; use Custom Metadata, Custom Settings, Named Credentials |
| Tests | `@IsTest`, `@TestSetup`, `Test.startTest/stopTest`, positive + negative + bulk, real assertions, 90%+ |
| Docs | ApexDoc on classes and public methods |
