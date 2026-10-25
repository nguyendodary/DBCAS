"""Database Design expansion, EASY band (levels 1-2).

Eight MCQs tagged to ER modeling / normalization and two SQL practicals. The
ER/NORM tags make every item eligible for assessment 4; because assessment 3's
concept set contains those concepts, the same items also count there. The
specific-concept depth for assessment 3 at this band already exists in questions
14-17, so no FD/1NF/2NF/3NF item is duplicated here.
"""

from lib import mcq, sqlq
from sources import (
    CHEN_1976,
    CODD_1971,
    PG_AGGREGATE,
    PG_JOIN_TUTORIAL,
    PG_SELECT,
    WATT_DB_DESIGN,
)

QUESTIONS = [
    mcq(
        "db-easy-weak-entity",
        ["DB-ER"],
        2,
        (
            "In an ER model, a dependent entity can exist only while its owning "
            "entity exists, and its identifying key includes the owner's "
            "primary key. Which relational mapping is correct?"
        ),
        [
            "Give the dependent table its own surrogate primary key and omit "
            "the owner key, because a surrogate key makes the owner unnecessary.",
            "Use a composite primary key made of the owner's primary key plus "
            "the dependent entity's partial key, with a foreign key to the "
            "owner.",
            "Store the dependent rows as a comma-separated list in a column of "
            "the owner table, because the dependency is one-to-many.",
            "Add a nullable foreign key to the owner and allow dependent rows "
            "that reference no owner, because NULL means 'not yet assigned'.",
        ],
        1,
        (
            "A weak entity is identified through its owner: the owner key is "
            "part of the weak entity's primary key and also a foreign key. The "
            "composite key prevents two owners from sharing partial-key values, "
            "and the foreign key plus deletion rules preserve existence "
            "dependence. A surrogate key alone does not encode the identifying "
            "relationship; a delimited list is non-atomic; and a nullable "
            "foreign key contradicts the stated existence dependency."
        ),
        [CHEN_1976, WATT_DB_DESIGN],
    ),
    mcq(
        "db-easy-one-to-many-fk",
        ["DB-ER"],
        2,
        (
            "An order must belong to exactly one customer, and a customer may "
            "place zero or more orders. Where should the foreign key be placed "
            "to represent this one-to-many relationship?"
        ),
        [
            "In the customer table, as order_id referencing orders, so that a "
            "customer row points at its latest order.",
            "In the orders table, as a NOT NULL customer_id referencing the "
            "customer primary key.",
            "In a separate junction table keyed by customer_id and order_id, "
            "because every relationship needs its own table.",
            "In the orders table, as duplicated customer_name and customer_city "
            "columns instead of a key.",
        ],
        1,
        (
            "On the many side, each order stores one customer key, so "
            "customer_id in orders can be NOT NULL and reference customer. "
            "Putting order_id in customer would allow at most one order per "
            "customer and creates a circular dependency. A junction table is "
            "needed for many-to-many, not one-to-many. Duplicating descriptive "
            "customer columns reintroduces update anomalies and does not "
            "enforce the relationship."
        ),
        [CHEN_1976, WATT_DB_DESIGN],
    ),
    mcq(
        "db-easy-deletion-anomaly",
        ["DB-NORM"],
        2,
        (
            "A supplier and the parts it supplies are stored in "
            "part(part_id, part_name, supplier_id, supplier_name, "
            "supplier_city). Deleting the last part supplied by a supplier also "
            "erases the only record of that supplier's name and city. Which "
            "anomaly is this?"
        ),
        [
            "An insert anomaly, because a new supplier cannot be recorded "
            "without a part.",
            "An update anomaly, because the supplier city is stored more than "
            "once.",
            "A deletion anomaly, because deleting a part row destroys unrelated "
            "supplier facts.",
            "A phantom-read anomaly, because a concurrent transaction sees a "
            "row that was never committed.",
        ],
        2,
        (
            "The row mixes two entities, part and supplier. Deleting the last "
            "part necessarily deletes the supplier information that has no "
            "separate home: that is a deletion anomaly. Insert anomalies and "
            "update anomalies are related redundancy problems, but the stated "
            "symptom is loss of facts on deletion. A phantom read is a "
            "transaction-isolation phenomenon and has nothing to do with schema "
            "design."
        ),
        [WATT_DB_DESIGN, CODD_1971],
    ),
    mcq(
        "db-easy-update-anomaly",
        ["DB-NORM"],
        2,
        (
            "An orders table repeats customer_phone on every order row. When a "
            "customer changes phone number, the application must update many "
            "rows, and a missed row leaves contradictory values. Which anomaly "
            "does this describe?"
        ),
        [
            "An update anomaly caused by storing the same fact in multiple "
            "places.",
            "A deletion anomaly caused by removing the last order.",
            "An insert anomaly caused by adding an order without a phone "
            "number.",
            "A serialization anomaly caused by concurrent transactions.",
        ],
        0,
        (
            "The same customer fact is repeated across rows, so one logical "
            "change needs many physical updates; missing one creates "
            "inconsistency. That is the definition of an update anomaly. "
            "Deletion and insert anomalies concern losing facts or being unable "
            "to record facts; serialization anomalies belong to concurrency "
            "control, not to the schema's redundancy."
        ),
        [WATT_DB_DESIGN, CODD_1971],
    ),
    mcq(
        "db-easy-multivalued-skill",
        ["DB-ER", "DB-1NF"],
        1,
        (
            "An employee may have several skills. Which design both models the "
            "relationship correctly and keeps attribute values atomic?"
        ),
        [
            "A skills TEXT column containing values such as 'SQL,Python,Go'.",
            "Three columns skill_1, skill_2 and skill_3, leaving unused columns "
            "NULL.",
            "A junction table employee_skill(employee_id, skill_id) whose "
            "primary key is (employee_id, skill_id), with foreign keys to both "
            "parent tables.",
            "A JSONB array column on employee, because PostgreSQL can index "
            "array elements.",
        ],
        2,
        (
            "A multivalued attribute becomes its own relation whose key combines "
            "the owner key and the value key; each cell then holds one value. A "
            "delimited string and a JSONB array both store several values in "
            "one cell, which is not atomic in the relational model even though "
            "PostgreSQL permits those types. Fixed skill_1..skill_3 columns are "
            "a repeating group and impose an arbitrary limit."
        ),
        [WATT_DB_DESIGN, CHEN_1976],
    ),
    mcq(
        "db-easy-normalization-goal",
        ["DB-NORM"],
        1,
        (
            "Which statement best describes the purpose of normalization?"
        ),
        [
            "It removes the need for joins by placing every fact in one table.",
            "It organizes attributes into relations so that redundancy and the "
            "resulting update anomalies are reduced while dependencies are "
            "preserved.",
            "It duplicates frequently read columns so that queries avoid "
            "aggregation.",
            "It guarantees that every query uses an index.",
        ],
        1,
        (
            "Normalization decomposes relations according to functional "
            "dependencies so that each fact is stored once, reducing insertion, "
            "update and deletion anomalies. It does not eliminate joins (good "
            "decompositions often require them), it is the opposite of adding "
            "redundant columns, and indexes are a physical performance concern "
            "unrelated to normal-form correctness."
        ),
        [WATT_DB_DESIGN, CODD_1971],
    ),
    mcq(
        "db-easy-total-participation",
        ["DB-ER"],
        2,
        (
            "Every loan must be associated with exactly one member, while a "
            "member may have no loans. Which relational constraint expresses "
            "the mandatory participation of loan in the relationship?"
        ),
        [
            "A NOT NULL member_id foreign key in the loan table referencing "
            "member.",
            "A UNIQUE member_id in the loan table, because every loan needs a "
            "distinct member.",
            "A foreign key from member to loan, so that each member row points "
            "at a loan.",
            "CHECK (member_id > 0) on the loan table.",
        ],
        0,
        (
            "Mandatory participation on the many side is enforced by making the "
            "foreign key NOT NULL: every loan row must name an existing member. "
            "UNIQUE would incorrectly restrict each member to one loan. Putting "
            "the foreign key in member reverses the relationship and cannot "
            "represent several loans per member. A numeric CHECK says nothing "
            "about existence of the referenced member."
        ),
        [CHEN_1976, PG_JOIN_TUTORIAL],
    ),
    mcq(
        "db-easy-repeating-group",
        ["DB-NORM", "DB-1NF"],
        2,
        (
            "The table contact(customer_id, phone_1, phone_2, phone_3) stores "
            "up to three phone numbers per customer and leaves unused columns "
            "NULL. Which normal form is most directly violated, and why?"
        ),
        [
            "First normal form, because the phone_1..phone_3 columns form a "
            "repeating group rather than atomic single-valued attributes.",
            "Second normal form, because phone_2 depends on only part of a "
            "composite key.",
            "Third normal form, because phone_3 is transitively dependent on "
            "the key.",
            "Boyce-Codd normal form, because a non-superkey determinant exists.",
        ],
        0,
        (
            "1NF requires each attribute position to hold one atomic value and "
            "forbids repeating groups. Numbered columns are a repeating group "
            "and also cap the number of phones. The table's key is the single "
            "attribute customer_id, so partial dependency (2NF) cannot arise "
            "here, and no transitive or non-superkey determinant is described; "
            "the defect is at the atomicity level."
        ),
        [WATT_DB_DESIGN, CODD_1971],
    ),
    sqlq(
        "db-easy-city-customer-count",
        ["DB-ER"],
        2,
        (
            "Table customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL, "
            "city TEXT) stores one row per customer. Return one row per city "
            "with columns city (TEXT) and customers (BIGINT), counting the "
            "customers in that city. Include a group for NULL city. Order by "
            "city ascending with NULLs last."
        ),
        "SELECT city, count(*) AS customers FROM customer GROUP BY city ORDER BY city NULLS LAST",
        [
            (
                "three_cities",
                False,
                "CREATE TABLE customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL, city TEXT);"
                "INSERT INTO customer VALUES "
                "(1,'An','Hanoi'),(2,'Binh','Da Nang'),(3,'Chi','Hanoi'),"
                "(4,'Dung',NULL),(5,'Em','Hue');",
            ),
            (
                "empty_customer",
                True,
                "CREATE TABLE customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL, city TEXT);",
            ),
        ],
        (
            "GROUP BY city forms one group per distinct non-NULL value and one "
            "group for all NULLs; count(*) counts rows in each group, not "
            "distinct customers, which is correct because customer_id is the "
            "primary key. NULLS LAST makes the NULL group deterministic. The "
            "empty dataset returns no rows, which is the correct result rather "
            "than an error."
        ),
        [PG_SELECT, PG_AGGREGATE],
    ),
    sqlq(
        "db-easy-order-owner-left-join",
        ["DB-ER"],
        2,
        (
            "Table customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL) "
            "and table orders(order_id INT PRIMARY KEY, customer_id INT, amount "
            "NUMERIC(10,2)). Return order_id (INT), name (TEXT) and amount for "
            "every order. If an order's customer_id has no matching customer, "
            "return the order with a NULL name. Order by order_id ascending."
        ),
        (
            "SELECT o.order_id, c.name, o.amount FROM orders o "
            "LEFT JOIN customer c ON c.customer_id = o.customer_id "
            "ORDER BY o.order_id"
        ),
        [
            (
                "orders_with_orphan",
                False,
                "CREATE TABLE customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL);"
                "CREATE TABLE orders(order_id INT PRIMARY KEY, customer_id INT, amount NUMERIC(10,2));"
                "INSERT INTO customer VALUES (1,'An'),(2,'An'),(3,'Binh');"
                "INSERT INTO orders VALUES (10,1,25.50),(11,2,10.00),(12,99,7.25),(13,NULL,3.00);",
            ),
            (
                "no_orders",
                True,
                "CREATE TABLE customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL);"
                "CREATE TABLE orders(order_id INT PRIMARY KEY, customer_id INT, amount NUMERIC(10,2));"
                "INSERT INTO customer VALUES (1,'An');",
            ),
        ],
        (
            "The relationship is optional from the order side in this dataset, "
            "so a LEFT JOIN keeps every order and produces NULL when no "
            "customer matches, including an orphan key and a NULL key. Duplicate "
            "customer names are not a problem because the join uses the key. "
            "With no orders the result is empty, and the column set is still "
            "determined by the SELECT list."
        ),
        [PG_JOIN_TUTORIAL, PG_SELECT],
    ),
]
