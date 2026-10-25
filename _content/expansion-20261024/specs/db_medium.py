"""Database Design expansion, MEDIUM band (level 3).

Ten MCQs each carry a normalization tag so assessment 4 can use all of them,
while the second concept tag (ER, FD, 1NF, 2NF, 3NF) gives assessment 3 the
depth its wider concept set needs. The two SQL practicals and the essay are
tagged ER/NORM, so the same plan serves both assessments.
"""

from lib import essay, mcq, sqlq
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
        "db-medium-closure",
        ["DB-FD", "DB-NORM"],
        3,
        (
            "Relation R(A,B,C,D) satisfies the functional dependencies A -> B "
            "and B -> C. Which statement is correct?"
        ),
        [
            "A is a candidate key because it determines B and C.",
            "The closure A+ is {A,B,C}, so A does not determine D and is not a "
            "superkey.",
            "The closure A+ is {A,B,C,D} because transitivity propagates to "
            "every attribute of the relation.",
            "D -> A must hold because A is not a candidate key.",
        ],
        1,
        (
            "Compute the attribute closure: start with {A}; A -> B adds B; "
            "B -> C adds C; no dependency has a left side contained in "
            "{A,B,C} that produces D. Therefore A+ = {A,B,C}, A is not a "
            "superkey, and no dependency implies D -> A. A candidate key must "
            "determine every attribute, which A does not."
        ),
        [WATT_DB_DESIGN, CODD_1971],
    ),
    mcq(
        "db-medium-candidate-keys",
        ["DB-FD", "DB-NORM"],
        3,
        (
            "Relation R(A,B,C,D) has functional dependencies AB -> C, C -> D "
            "and D -> A. Which set is exactly the set of candidate keys?"
        ),
        [
            "{AB}",
            "{AB, BC}",
            "{AB, BC, BD}",
            "{AB, AC}",
        ],
        2,
        (
            "AB+ = {A,B,C,D}, so AB is a key and neither A nor B alone is. "
            "BC+ = {B,C,D,A}, so BC is a key. BD+ = {B,D,A,C}: D -> A adds A, "
            "then AB -> C adds C, so BD is also a key. AC+ = {A,C,D} and does "
            "not contain B, so AC is not a key. The three keys are minimal "
            "because no single attribute of any of them determines all four "
            "attributes."
        ),
        [WATT_DB_DESIGN, CODD_1971],
    ),
    mcq(
        "db-medium-partial-dependency",
        ["DB-2NF", "DB-NORM"],
        3,
        (
            "The relation enrollment(student_id, course_id, course_title, "
            "grade) has primary key (student_id, course_id) and the functional "
            "dependency course_id -> course_title. Which statement identifies "
            "the 2NF violation and its correct repair?"
        ),
        [
            "There is no violation, because course_title is determined by the "
            "full primary key through course_id.",
            "course_title depends on course_id, a proper subset of the "
            "composite key; move (course_id, course_title) to a course "
            "relation and keep (student_id, course_id, grade) in enrollment.",
            "grade depends on the full key, so grade must be moved to its own "
            "relation to achieve 2NF.",
            "The relation is already in 3NF because every non-key attribute "
            "depends on the primary key.",
        ],
        1,
        (
            "2NF forbids a non-prime attribute from depending on part of a "
            "candidate key. course_title is non-prime and depends on course_id "
            "alone, a proper subset of {student_id, course_id}. Removing that "
            "partial dependency yields course(course_id, course_title) and "
            "enrollment(student_id, course_id, grade). Depending on the full "
            "key is exactly what is allowed; grade is not the problem."
        ),
        [WATT_DB_DESIGN, CODD_1971],
    ),
    mcq(
        "db-medium-3nf-not-bcnf",
        ["DB-3NF", "DB-FD"],
        3,
        (
            "Relation R(A,B,C) has functional dependencies AB -> C and C -> B. "
            "The candidate keys are AB and AC. Which statement is correct?"
        ),
        [
            "The relation is in BCNF because every attribute is prime.",
            "The relation is in 3NF but not BCNF because C -> B has a "
            "non-superkey determinant and B is prime.",
            "The relation violates 2NF because C -> B is a partial dependency.",
            "The relation violates 1NF because B appears on both sides of a "
            "functional dependency.",
        ],
        1,
        (
            "3NF permits a functional dependency X -> Y when X is a superkey "
            "or every attribute of Y is prime. C is not a superkey, but B is "
            "part of candidate key AB, so the dependency is allowed by 3NF. "
            "BCNF has no prime-attribute exception, so C -> B violates BCNF. "
            "2NF concerns dependencies on part of a composite key by non-prime "
            "attributes; B is prime, and 1NF is about atomic values, not "
            "repeated symbols."
        ),
        [WATT_DB_DESIGN, CODD_1971],
    ),
    mcq(
        "db-medium-nonatomic-list",
        ["DB-1NF", "DB-NORM"],
        3,
        (
            "The relation order_item(order_id, items) stores a value such as "
            "'pen,notebook,stapler' in items. Which statement is correct?"
        ),
        [
            "1NF holds because each row contains one string value in the items "
            "column.",
            "The relation violates 1NF; model it as order_line(order_id, "
            "product_id, quantity) with primary key (order_id, product_id).",
            "The relation violates 2NF only, because product names depend on "
            "part of the key.",
            "The relation violates 3NF because item names are transitively "
            "dependent on order_id.",
        ],
        1,
        (
            "A value that packs several items into one cell is not atomic, so "
            "the relation is not in 1NF regardless of the string type. The "
            "repair is a child relation with one row per order-product pair, "
            "keyed by both identifiers. 2NF and 3NF presuppose 1NF and concern "
            "dependencies among attributes, not multiple values hidden inside "
            "one attribute."
        ),
        [WATT_DB_DESIGN, CODD_1971],
    ),
    mcq(
        "db-medium-one-to-one-mapping",
        ["DB-ER", "DB-NORM"],
        3,
        (
            "Every laptop must be assigned to exactly one employee, and an "
            "employee has at most one laptop. Laptop participation is total. "
            "Which mapping avoids a nullable unique foreign key?"
        ),
        [
            "Give laptop a NOT NULL UNIQUE employee_id referencing employee.",
            "Give employee a nullable UNIQUE laptop_id referencing laptop.",
            "Merge employee and laptop into one table whose laptop columns are "
            "nullable.",
            "Create a junction table employee_laptop keyed by both employee_id "
            "and laptop_id.",
        ],
        0,
        (
            "The foreign key belongs on the side with total participation: "
            "laptop.employee_id NOT NULL guarantees every laptop has an owner, "
            "and UNIQUE guarantees an employee owns at most one laptop. Placing "
            "the key on employee makes it nullable for employees without a "
            "laptop. Merging imposes wide nullable columns and mixes entities; "
            "a junction table models many-to-many and would allow several "
            "owners per laptop."
        ),
        [CHEN_1976, WATT_DB_DESIGN],
    ),
    mcq(
        "db-medium-lossless-common-attribute",
        ["DB-NORM", "DB-FD"],
        3,
        (
            "Relation R(A,B,C) satisfies B -> A and is decomposed into "
            "R1(A,B) and R2(B,C). Is the decomposition lossless, and why?"
        ),
        [
            "It is always lossless because the decomposition preserves all "
            "three attribute names.",
            "It is lossless because the common attribute B is a key of R1: "
            "B -> A holds in R1.",
            "It is lossy because A and C end up in different relations.",
            "It is lossless only if B -> C also holds.",
        ],
        1,
        (
            "For a binary decomposition, the join is lossless if the common "
            "attributes form a superkey of at least one side. The common "
            "attribute is B, and B -> A means B determines every attribute of "
            "R1(A,B), so B is a key of R1. Therefore projecting onto {A,B} and "
            "{B,C} and joining back cannot create spurious tuples. Attribute "
            "preservation is not the same property as losslessness, and B -> C "
            "is irrelevant."
        ),
        [WATT_DB_DESIGN, CODD_1971],
    ),
    mcq(
        "db-medium-ternary-association",
        ["DB-ER"],
        3,
        (
            "A supplier supplies parts to projects. Quantity is recorded for a "
            "specific supplier, part and project, and one supplier-part pair "
            "can supply several projects. Which schema represents this "
            "relationship correctly?"
        ),
        [
            "Three binary relations supplier_part, part_project and "
            "supplier_project, none of which can hold quantity for the triple.",
            "A relation supply(supplier_id, part_id, project_id, quantity) "
            "with a composite primary key over the three keys and a foreign key "
            "to each parent.",
            "Add project_id to the part table and repeat each part row once per "
            "project.",
            "Store a list of project identifiers in an array column on "
            "supplier.",
        ],
        1,
        (
            "The fact 'this supplier supplied this quantity of this part to "
            "this project' depends on all three entities, so the associative "
            "relation's key is the triple. Binary tables cannot record a "
            "quantity that is meaningful only for the triple. Repeating parts "
            "per project duplicates part facts, and an array hides a "
            "multivalued relationship in a non-atomic value."
        ),
        [CHEN_1976, WATT_DB_DESIGN],
    ),
    mcq(
        "db-medium-augmentation",
        ["DB-FD"],
        3,
        (
            "Given only the functional dependency A -> B, which dependency "
            "follows by the augmentation axiom?"
        ),
        [
            "B -> A",
            "AC -> BC",
            "A -> C",
            "C -> B",
        ],
        1,
        (
            "Augmentation says that if X -> Y holds, then XZ -> YZ holds for "
            "any attribute set Z. Adding C to both sides of A -> B yields "
            "AC -> BC. B -> A would require a different dependency; A -> C "
            "cannot be inferred because C appears nowhere in the premise; "
            "C -> B is not implied either."
        ),
        [WATT_DB_DESIGN, CODD_1971],
    ),
    mcq(
        "db-medium-3nf-synthesis",
        ["DB-3NF", "DB-NORM"],
        3,
        (
            "Which statement about 3NF synthesis and BCNF decomposition is "
            "correct?"
        ),
        [
            "Every BCNF decomposition preserves all functional dependencies.",
            "A 3NF synthesis can be lossless and dependency-preserving, while "
            "a BCNF decomposition is lossless but may lose a functional "
            "dependency.",
            "3NF forbids partial dependencies but intentionally allows "
            "transitive dependencies among non-prime attributes.",
            "BCNF allows a non-superkey determinant whenever the dependent "
            "attribute is prime.",
        ],
        1,
        (
            "The 3NF synthesis algorithm produces a lossless, "
            "dependency-preserving decomposition. BCNF is stricter and a "
            "lossless BCNF decomposition may split a dependency across "
            "relations, so dependency preservation is not guaranteed. 3NF also "
            "forbids transitive dependencies of non-prime attributes on a "
            "non-superkey; BCNF has no prime-attribute exception at all."
        ),
        [WATT_DB_DESIGN, CODD_1971],
    ),
    sqlq(
        "db-medium-email-audit",
        ["DB-NORM"],
        3,
        (
            "Table customer_email(row_id INT PRIMARY KEY, customer_id INT NOT "
            "NULL, email TEXT) records contact rows, and the same customer may "
            "appear more than once. Return email (TEXT), copies (BIGINT: rows "
            "with that email) and ids (BIGINT: distinct customer IDs with that "
            "email) for every non-NULL email used by more than one distinct "
            "customer. Order by copies descending, then email ascending."
        ),
        (
            "SELECT email, count(*) AS copies, count(DISTINCT customer_id) AS ids "
            "FROM customer_email WHERE email IS NOT NULL GROUP BY email "
            "HAVING count(DISTINCT customer_id) > 1 "
            "ORDER BY copies DESC, email"
        ),
        [
            (
                "shared_and_unique",
                False,
                "CREATE TABLE customer_email(row_id INT PRIMARY KEY, customer_id INT NOT NULL, email TEXT);"
                "INSERT INTO customer_email VALUES "
                "(1,1,'an@example.edu'),(2,2,'an@example.edu'),"
                "(3,3,'binh@example.edu'),(4,4,'chi@example.edu'),"
                "(5,5,NULL);",
            ),
            (
                "repeat_same_customer",
                True,
                "CREATE TABLE customer_email(row_id INT PRIMARY KEY, customer_id INT NOT NULL, email TEXT);"
                "INSERT INTO customer_email VALUES "
                "(1,1,'dup@example.edu'),(2,1,'dup@example.edu'),"
                "(3,2,'dup@example.edu'),(4,3,NULL),(5,4,NULL);",
            ),
        ],
        (
            "The audit looks for one email attached to several customers, which "
            "is evidence that email is not a key and that the relation stores "
            "redundant contact facts. count(*) counts rows, while "
            "count(DISTINCT customer_id) counts customers; the edge dataset has "
            "three rows but two customers, so both numbers are needed. NULL "
            "emails are excluded because a NULL is not a shared value."
        ),
        [PG_SELECT, PG_AGGREGATE],
    ),
    sqlq(
        "db-medium-customer-order-totals",
        ["DB-ER"],
        3,
        (
            "Table customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL) "
            "and table orders(order_id INT PRIMARY KEY, customer_id INT, amount "
            "NUMERIC(10,2)). Return customer_id, name, order_count (BIGINT) and "
            "total (NUMERIC, 0 when there are no orders or all amounts are "
            "NULL) for every customer, including customers with no orders. "
            "Order by customer_id ascending."
        ),
        (
            "SELECT c.customer_id, c.name, count(o.order_id) AS order_count, "
            "coalesce(sum(o.amount), 0) AS total "
            "FROM customer c LEFT JOIN orders o ON o.customer_id = c.customer_id "
            "GROUP BY c.customer_id, c.name ORDER BY c.customer_id"
        ),
        [
            (
                "mixed_orders",
                False,
                "CREATE TABLE customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL);"
                "CREATE TABLE orders(order_id INT PRIMARY KEY, customer_id INT, amount NUMERIC(10,2));"
                "INSERT INTO customer VALUES (1,'An'),(2,'An'),(3,'Binh');"
                "INSERT INTO orders VALUES (10,1,5.00),(11,1,NULL),(12,2,7.50);",
            ),
            (
                "no_orders",
                True,
                "CREATE TABLE customer(customer_id INT PRIMARY KEY, name TEXT NOT NULL);"
                "CREATE TABLE orders(order_id INT PRIMARY KEY, customer_id INT, amount NUMERIC(10,2));"
                "INSERT INTO customer VALUES (1,'An'),(2,'Binh');",
            ),
        ],
        (
            "A LEFT JOIN keeps customers without orders. count(o.order_id) "
            "ignores the NULL produced by the join, so the count is 0, while "
            "count(*) would incorrectly return 1. sum ignores NULL amounts, and "
            "coalesce turns the all-NULL or no-row sum into 0. Grouping by both "
            "customer_id and name keeps the query valid even though names are "
            "not unique."
        ),
        [PG_JOIN_TUTORIAL, PG_AGGREGATE],
    ),
    essay(
        "db-medium-library-normalization",
        ["DB-ER", "DB-NORM", "DB-FD"],
        3,
        (
            "A library stores loans in loan(member_id, member_name, "
            "member_city, book_id, book_title, book_author, loan_date, "
            "due_date). The functional dependencies are: member_id -> "
            "member_name, member_city; book_id -> book_title, book_author; and "
            "(member_id, book_id, loan_date) -> due_date. A member may borrow "
            "the same book again on a different date. (a) Identify the "
            "candidate key. (b) Determine the highest normal form and name each "
            "dependency that prevents the next form. (c) Decompose the relation "
            "into 3NF, listing keys and foreign keys. (d) Explain why the "
            "decomposition is lossless-join and dependency-preserving."
        ),
        (
            "(a) The candidate key is {member_id, book_id, loan_date}. It "
            "determines due_date directly and determines the member and book "
            "attributes through member_id and book_id; each proper subset "
            "loses at least one attribute, so it is minimal. "
            "(b) The highest normal form is 1NF. 2NF fails because the "
            "non-prime attributes member_name and member_city depend on "
            "member_id alone, and book_title and book_author depend on book_id "
            "alone; both are proper subsets of the composite key. Because 2NF "
            "fails, 3NF is not reached. "
            "(c) member(member_id PK, member_name, member_city); "
            "book(book_id PK, book_title, book_author); "
            "loan(member_id PK/FK REFERENCES member, book_id PK/FK REFERENCES "
            "book, loan_date PK, due_date). "
            "(d) Each split removes a partial dependency and joins back on a "
            "common attribute that is a key of one side (member_id in member, "
            "book_id in book), so each step is lossless by the common-attribute "
            "test. Dependency preservation holds because member_id -> name, "
            "city is enforced in member; book_id -> title, author is enforced "
            "in book; and the key dependency on all three attributes is "
            "enforced in loan."
        ),
        (
            "The composite key includes the loan date because the same member "
            "can borrow the same book again. Partial dependencies on member_id "
            "and book_id keep the original relation in 1NF only. Separating "
            "member, book and loan removes them; the common attributes are keys "
            "of the reference relations, so the decomposition is lossless, and "
            "each dependency is enforceable inside one relation."
        ),
        (
            "Identifies no candidate key or a key missing loan_date, and gives "
            "no valid normal-form argument; the decomposition, if present, is "
            "unusable or loses the loan fact.",
            "Names a plausible key but omits at least one partial dependency or "
            "mislabels the highest normal form; the decomposition separates "
            "some but not all entity facts, or keys and foreign keys are "
            "missing.",
            "Correct key and identifies both partial dependencies; decomposes "
            "into member, book and loan with correct keys, but the lossless or "
            "dependency-preservation justification is incomplete.",
            "Fully correct: key {member_id, book_id, loan_date} with a "
            "minimality argument; highest form 1NF because of the partial "
            "dependencies member_id -> member attributes and book_id -> book "
            "attributes; decomposition member, book and loan with correct "
            "primary and foreign keys; lossless by the common-attribute-key "
            "test on each split; dependency-preserving because every "
            "functional dependency is enforced inside a single relation.",
        ),
        [WATT_DB_DESIGN, CODD_1971],
    ),
    mcq(
        "db-medium-optional-self-reference",
        ["DB-ER", "DB-NORM"],
        3,
        (
            "A customer may have been referred by another customer, but many "
            "customers have no referrer. Which schema models this optional "
            "self-referencing relationship correctly?"
        ),
        [
            "customer(customer_id PK, name, referred_by_id INT NOT NULL "
            "REFERENCES customer).",
            "customer(customer_id PK, name, referred_by_id INT NULL REFERENCES "
            "customer(customer_id)).",
            "customer(customer_id PK, name, referred_by_name TEXT).",
            "A referrer table with two NOT NULL foreign keys, where every "
            "customer must appear.",
        ],
        1,
        (
            "Optional participation permits NULL, so the self-referencing "
            "foreign key must be nullable; roots simply store NULL. A NOT NULL "
            "self-reference makes the first customer impossible to insert. "
            "Storing a name instead of a key loses identity and reintroduces "
            "update anomalies. A mandatory referrer table contradicts the "
            "statement that many customers have no referrer."
        ),
        [CHEN_1976, WATT_DB_DESIGN],
    ),
    mcq(
        "db-medium-residual-transitive",
        ["DB-3NF", "DB-NORM"],
        3,
        (
            "A relation is in 2NF but not in 3NF because a non-prime attribute "
            "depends on another non-prime attribute. Which operational problem "
            "remains?"
        ),
        [
            "The dependent fact is repeated for every determinant value, so "
            "changing it can require several updates and missed rows create "
            "inconsistency.",
            "A single cell can contain several values, so the relation is not "
            "atomic.",
            "A non-prime attribute depends on only part of a composite key.",
            "No problem remains, because 2NF and 3NF are equivalent whenever "
            "the key is composite.",
        ],
        0,
        (
            "The transitive dependency is redundancy: the dependent fact is "
            "stored once per determinant occurrence, creating update, insert "
            "and delete anomalies. Non-atomic values are a 1NF problem; "
            "dependence on part of a composite key is the 2NF problem already "
            "removed; and 2NF does not imply 3NF for any key shape."
        ),
        [WATT_DB_DESIGN, CODD_1971],
    ),
]
