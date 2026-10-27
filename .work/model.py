"""Single source for the explanatory note and editable diagrams."""

TABLES = [
    ('BANK_USERS', 'Учетные записи', [
        ('PK','user_id','NUMBER(19)'), ('UK','oracle_username','VARCHAR2(128 CHAR)'),
        ('UK','login','VARCHAR2(64 CHAR)'), ('','is_blocked','NUMBER(1)'),
        ('','created_at','TIMESTAMP(6) WITH TIME ZONE')]),
    ('BANK_ROLES', 'Роли доступа', [
        ('PK','role_id','NUMBER(19)'), ('UK','role_code','VARCHAR2(20 CHAR)'),
        ('','role_name','VARCHAR2(80 CHAR)')]),
    ('BANK_USER_ROLES', 'Назначения ролей', [
        ('PK, FK','user_id','NUMBER(19)'), ('PK, FK','role_id','NUMBER(19)')]),
    ('BANK_CLIENTS', 'Клиенты', [
        ('PK','client_id','NUMBER(19)'), ('FK, UK','user_id','NUMBER(19)'),
        ('','full_name_enc','RAW(2000)'), ('','document_enc','RAW(512)'),
        ('UK','document_hmac','RAW(32)'), ('','phone_enc','RAW(512)'),
        ('','email_enc','RAW(2000)'), ('','key_version','NUMBER(4)')]),
    ('BANK_EMPLOYEES', 'Сотрудники', [
        ('PK','employee_id','NUMBER(19)'), ('FK, UK','user_id','NUMBER(19)'),
        ('','full_name_enc','RAW(2000)'), ('','position_name','VARCHAR2(100 CHAR)'),
        ('','key_version','NUMBER(4)')]),
    ('BANK_CURRENCIES', 'Валюты', [
        ('PK','currency_code','CHAR(3 CHAR)'), ('','currency_name','VARCHAR2(60 CHAR)')]),
    ('BANK_ACCOUNTS', 'Банковские счета', [
        ('PK','account_id','NUMBER(19)'), ('FK','client_id','NUMBER(19)'),
        ('FK','currency_code','CHAR(3 CHAR)'), ('UK','account_no','VARCHAR2(34 CHAR)'),
        ('','status','VARCHAR2(10 CHAR)'), ('','opening_balance','NUMBER(18,2)'),
        ('','balance','NUMBER(18,2)'), ('','opened_at','TIMESTAMP(6) WITH TIME ZONE'),
        ('','closed_at','TIMESTAMP(6) WITH TIME ZONE'), ('FK','opened_by','NUMBER(19)')]),
    ('BANK_CARDS', 'Банковские карты', [
        ('PK','card_id','NUMBER(19)'), ('FK','account_id','NUMBER(19)'),
        ('','pan_enc','RAW(128)'), ('UK','pan_hmac','RAW(32)'),
        ('','pan_last4','CHAR(4 CHAR)'), ('','expires_at','DATE'),
        ('','status','VARCHAR2(10 CHAR)'), ('','key_version','NUMBER(4)'),
        ('FK','issued_by','NUMBER(19)')]),
    ('BANK_OPERATION_TYPES', 'Типы операций', [
        ('PK','type_code','VARCHAR2(12 CHAR)'), ('','type_name','VARCHAR2(80 CHAR)')]),
    ('BANK_OPERATIONS', 'Проведенные операции', [
        ('PK','operation_id','NUMBER(19)'), ('FK','initiator_user_id','NUMBER(19)'),
        ('FK','debit_account_id','NUMBER(19)'), ('FK','credit_account_id','NUMBER(19)'),
        ('FK','type_code','VARCHAR2(12 CHAR)'), ('','amount','NUMBER(18,2)'),
        ('','purpose','VARCHAR2(250 CHAR)'), ('UK*','request_id','VARCHAR2(64 CHAR)'),
        ('','created_at','TIMESTAMP(6) WITH TIME ZONE')]),
    ('BANK_ACCOUNT_LIMITS', 'Лимиты счета', [
        ('PK, FK','account_id','NUMBER(19)'), ('','per_operation_limit','NUMBER(18,2)'),
        ('','daily_limit','NUMBER(18,2)')]),
    ('BANK_AUDIT_LOG', 'Журнал аудита', [
        ('PK','audit_id','NUMBER(19)'), ('FK','actor_user_id','NUMBER(19)'),
        ('','oracle_username','VARCHAR2(128 CHAR)'), ('','action_code','VARCHAR2(40 CHAR)'),
        ('','object_type','VARCHAR2(30 CHAR)'), ('','object_id','NUMBER(19)'),
        ('','event_time','TIMESTAMP(6) WITH TIME ZONE'), ('','outcome','VARCHAR2(10 CHAR)'),
        ('','request_id','VARCHAR2(64 CHAR)'), ('','error_code','NUMBER(10)')]),
]

DESCRIPTIONS = {
 'BANK_USERS':'Соответствие прикладного пользователя учетной записи Oracle; признак блокировки и дата регистрации. Пароль в таблице не хранится.',
 'BANK_ROLES':'Коды ADMIN, EMPLOYEE и CLIENT и их наименования. Справочник не содержит технических полномочий владельца схемы.',
 'BANK_USER_ROLES':'Связь пользователей с ролями. Пара (user_id, role_id) является составным первичным ключом.',
 'BANK_CLIENTS':'Профиль клиента: зашифрованные Ф.И.О., документ, телефон и электронная почта; поисковый HMAC документа и версия ключей.',
 'BANK_EMPLOYEES':'Профиль сотрудника, его учетная запись, зашифрованные Ф.И.О. и должность.',
 'BANK_CURRENCIES':'Разрешенные валюты BYN, USD и EUR. В границах проекта суммы всех трех валют имеют два десятичных разряда.',
 'BANK_ACCOUNTS':'Владелец и валюта счета, уникальный номер, состояние, начальный и текущий остатки, даты открытия и закрытия.',
 'BANK_CARDS':'Принадлежность карты счету, шифротекст PAN, поисковый HMAC, последние четыре цифры, срок действия и состояние.',
 'BANK_OPERATION_TYPES':'Типы TRANSFER и PAYMENT. Перевод и платеж различаются назначением, но используют общий транзакционный механизм.',
 'BANK_OPERATIONS':'Неизменяемые сведения о проведенных операциях: инициатор, два счета, сумма, назначение, идентификатор запроса и время.',
 'BANK_ACCOUNT_LIMITS':'Разовый и суточный лимиты расходных операций. Строка создается одновременно со счетом.',
 'BANK_AUDIT_LOG':'Автор, действие, объект, время и результат обращения. Конфиденциальные значения и ключи в журнал не попадают.',
}

# The compact inventory is complemented by the detailed prose and both diagrams.
DESCRIPTIONS.update({
 'BANK_USERS':'Учетная запись Oracle, логин, блокировка и дата регистрации. Пароль в таблице не хранится.',
 'BANK_ROLES':'Справочник ролей ADMIN, EMPLOYEE и CLIENT.',
 'BANK_USER_ROLES':'Назначения ролей; составной первичный ключ (user_id, role_id).',
 'BANK_CLIENTS':'Зашифрованный профиль клиента, HMAC документа и версия ключей.',
 'BANK_EMPLOYEES':'Учетная запись, зашифрованные Ф.И.О. и должность сотрудника.',
 'BANK_CURRENCIES':'Справочник валют BYN, USD и EUR.',
 'BANK_ACCOUNTS':'Владелец, валюта, номер, состояние, остатки и даты обслуживания счета.',
 'BANK_CARDS':'Связанный счет, шифротекст и HMAC PAN, последние четыре цифры, срок и состояние.',
 'BANK_OPERATION_TYPES':'Справочник типов TRANSFER и PAYMENT.',
 'BANK_OPERATIONS':'Инициатор, два счета, сумма, назначение, идентификатор запроса и время проведения.',
 'BANK_ACCOUNT_LIMITS':'Разовый и суточный лимиты расходных операций счета.',
 'BANK_AUDIT_LOG':'Автор, действие, объект, время и результат обращения без конфиденциальных значений.',
})

RELATIONS = [
 ('BANK_USERS','BANK_USER_ROLES','user_id','1','0..N'),
 ('BANK_ROLES','BANK_USER_ROLES','role_id','1','0..N'),
 ('BANK_USERS','BANK_CLIENTS','user_id','1','0..1'),
 ('BANK_USERS','BANK_EMPLOYEES','user_id','1','0..1'),
 ('BANK_USERS','BANK_AUDIT_LOG','actor_user_id','0..1','0..N'),
 ('BANK_CLIENTS','BANK_ACCOUNTS','client_id','1','0..N'),
 ('BANK_CURRENCIES','BANK_ACCOUNTS','currency_code','1','0..N'),
 ('BANK_EMPLOYEES','BANK_ACCOUNTS','opened_by','1','0..N'),
 ('BANK_ACCOUNTS','BANK_CARDS','account_id','1','0..N'),
 ('BANK_EMPLOYEES','BANK_CARDS','issued_by','1','0..N'),
 ('BANK_ACCOUNTS','BANK_ACCOUNT_LIMITS','account_id','1','0..1'),
 ('BANK_ACCOUNTS','BANK_OPERATIONS','debit_account_id','1','0..N'),
 ('BANK_ACCOUNTS','BANK_OPERATIONS','credit_account_id','1','0..N'),
 ('BANK_OPERATION_TYPES','BANK_OPERATIONS','type_code','1','0..N'),
 ('BANK_USERS','BANK_OPERATIONS','initiator_user_id','1','0..N'),
]

SOURCES = [
 ('Oracle Database PL/SQL Packages and Types Reference 19c. DBMS_CRYPTO', 'https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/DBMS_CRYPTO.html'),
 ('Oracle Database PL/SQL Language Reference 19c. Invoker’s Rights and Definer’s Rights', 'https://docs.oracle.com/en/database/oracle/oracle-database/19/lnpls/invokers-rights-and-definers-rights-authid-property.html'),
 ('Oracle Database SQL Language Reference 19c. SELECT', 'https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/SELECT.html'),
 ('Oracle Database SQL Language Reference 19c. CREATE INDEX', 'https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/CREATE-INDEX.html'),
 ('Oracle Database JSON Developer’s Guide 19c. SQL/JSON Function JSON_TABLE', 'https://docs.oracle.com/en/database/oracle/oracle-database/19/adjsn/function-JSON_TABLE.html'),
 ('Oracle Database JSON Developer’s Guide 19c. Generation of JSON Data with SQL/JSON Functions', 'https://docs.oracle.com/en/database/oracle/oracle-database/19/adjsn/generation.html'),
]
