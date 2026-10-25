"""Database Design expansion, HARD band (levels 4-5).

Ten multi-step MCQs and two auditing SQL practicals, all tagged to ER or
normalization so assessment 4 remains feasible, plus a decomposition essay.
The specific FD/1NF/2NF/3NF tags supply assessment 3's wider coverage.
"""

from lib import essay, mcq, sqlq
from sources import (
    CHEN_1976,
    CODD_1971,
    PG_AGGREGATE,
    PG_ARRAYS,
    PG_QUERIES_WITH,
    PG_SELECT,
    WATT_DB_DESIGN,
)

QUESTIONS = [
    mcq(
        "db-hard-bcnf-dependency-loss",
        ["DB-FD", "DB-3NF", "DB-NORM"],
        4,
        (
            "Relation R(A,B,C,D) has functional dependencies AB -> CD and "
            "D -> A. A BCNF decomposition produces R1(A,D) and R2(B,C,D). "
            "Which statement is correct?"
        ),
        [
            "The decomposition is lossless and preserves AB -> CD.",
            "The decomposition is lossless but does not preserve AB -> CD.",
            "The decomposition is lossy because A and B are placed in "
            "different relations.",
            "No BCNF decomposition of this relation exists, so the question is "
            "ill-posed.",
        ],
        1,
        (
            "The candidate keys are AB and BD: AB+ is all attributes, and BD+ "
            "reaches A through D -> A and then C through AB -> C. D -> A "
            "violates BCNF. The split has common attribute D, and D -> A makes "
            "D a key of R1, so the join is lossless. R2 has no nontrivial "
            "projected dependency, but AB -> CD cannot be checked inside either "
            "relation because it needs A from R1 and B,C,D from R2. BCNF "
            "decompositions therefore need not preserve dependencies."
        ),
        [WATT_DB_DESIGN, CODD_1971],
    ),
    mcq(
        "db-hard-four-candidate-keys",
        ["DB-FD", "DB-NORM"],
        5,
        (
            "Relation R(A,B,C,D,E) satisfies AB -> C, C -> D, D -> E and "
            "E -> B. Which set is exactly the set of candidate keys?"
        ),
        [
            "{AB}",
            "{AB, AC}",
            "{AB, AC, AD, AE}",
            "{AB, AC, AD, AE, BC}",
        ],
        2,
        (
            "AB+ = {A,B,C,D,E}. AC+ reaches D through C -> D, E through D -> E, "
            "and B through E -> B, so AC is a key. AD+ reaches E through D -> E, "
            "B through E -> B, and C through AB -> C, so AD is a key. AE+ "
            "reaches B through E -> B, C through AB -> C, and D through C -> D, "
            "so AE is a key. No pair without A determines all attributes: BC+ "
            "lacks A and every other pair is smaller. Hence exactly AB, AC, AD "
            "and AE are minimal keys."
        ),
        [WATT_DB_DESIGN, CODD_1971],
    ),
    mcq(
        "db-hard-3nf-synthesis",
        ["DB-FD", "DB-3NF", "DB-NORM"],
        4,
        (
            "Relation R(A,B,C,D,E) has functional dependencies AB -> C, "
            "C -> D and D -> E. The only candidate key is AB. Which set of "
            "relations is a correct 3NF synthesis of R?"
        ),
        [
            "R1(A,B,C), R2(C,D), R3(D,E).",
            "R1(A,B), R2(C,D,E).",
            "R(A,B,C,D,E) unchanged, because the dependencies form a chain.",
            "R1(A,C), R2(B,D), R3(C,E).",
        ],
        0,
        (
            "The given FDs form a minimal cover, so synthesis creates one "
            "relation per dependency: (A,B,C), (C,D), (D,E). The candidate key "
            "AB is contained in R1, so no extra key relation is needed. Each "
            "relation's determinant is a key of that relation, so the result is "
            "in BCNF, lossless and dependency-preserving. Option B loses AB -> C; "
            "the unchanged relation is not in 3NF because C -> D and D -> E are "
            "transitive; option D does not preserve any of the original "
            "dependencies."
        ),
        [WATT_DB_DESIGN, CODD_1971],
    ),
    mcq(
        "db-hard-lossless-key-test",
        ["DB-NORM", "DB-FD"],
        4,
        (
            "Relation R(A,B,C) satisfies B -> C and is decomposed into R1(A,B) "
            "and R2(B,C). Which functional dependency is the reason the "
            "decomposition is lossless?"
        ),
        [
            "A -> B, because A must determine the other side.",
            "B -> C, because B is then a key of R2.",
            "C -> A, because A and C must be related.",
            "No functional dependency is needed; every binary decomposition "
            "that keeps all attributes is lossless.",
        ],
        1,
        (
            "The common attribute is B. Losslessness requires the common "
            "attributes to be a superkey of at least one projection. B -> C "
            "means B determines every attribute of R2(B,C), so B is a key of "
            "R2 and the join cannot invent tuples. Attribute preservation alone "
            "does not guarantee losslessness, and no dependency on A or C is "
            "given."
        ),
        [WATT_DB_DESIGN, CODD_1971],
    ),
    mcq(
        "db-hard-array-1nf",
        ["DB-1NF", "DB-NORM"],
        4,
        (
            "A PostgreSQL table stores tags TEXT[] with several tag values in "
            "one row. Relationally, which statement is correct?"
        ),
        [
            "The table is in 1NF because PostgreSQL arrays are a defined column "
            "type with element-level operators.",
            "The column holds a non-atomic value; relational 1NF requires a "
            "child table such as tag(entity_id, tag), even though PostgreSQL "
            "accepts and indexes arrays.",
            "The table violates 2NF because each tag depends on part of a "
            "composite primary key.",
            "The table is automatically in 3NF because array elements cannot "
            "participate in functional dependencies.",
        ],
        1,
        (
            "1NF is a relational-model property: each attribute position holds "
            "a single value. PostgreSQL's array type is a deliberate extension "
            "that permits non-1NF storage, not evidence of atomicity. A child "
            "relation with one tag per row restores 1NF and supports "
            "constraints, joins and dependency reasoning. There is no composite "
            "key described here, and array use neither implies nor prevents 3NF."
        ),
        [PG_ARRAYS, WATT_DB_DESIGN],
    ),
    mcq(
        "db-hard-specialization-mapping",
        ["DB-ER"],
        4,
        (
            "Person is specialized into Employee and Contractor. A person may "
            "be both, and every person must be at least one of the two. Which "
            "mapping enforces the model most faithfully in PostgreSQL?"
        ),
        [
            "Create employee and contractor tables that each repeat all person "
            "attributes, with no shared person table.",
            "Create person(person_id PK), employee(person_id PK/FK REFERENCES "
            "person) and contractor(person_id PK/FK REFERENCES person); the "
            "separate subtype rows allow overlap, while total participation "
            "needs a trigger or a role table because plain foreign keys cannot "
            "require at least one subtype row.",
            "Create one person table with nullable employee and contractor "
            "columns, which allows a person to be both.",
            "Create person_role(person_id, role) with UNIQUE(person_id) so each "
            "person has exactly one role.",
        ],
        1,
        (
            "Shared attributes belong in the supertype, and each subtype table "
            "references it with the same primary key, so a person can appear in "
            "both subtype tables (overlapping specialization). A foreign key "
            "from subtype to supertype enforces that subtype rows have a person, "
            "but SQL cannot enforce the reverse 'every person has a subtype' "
            "constraint; that requires a trigger, assertion-like check, or a "
            "role table. Duplicated subtype tables lose identity; nullable role "
            "columns cannot represent both roles independently; the UNIQUE "
            "constraint in option D forbids overlap."
        ),
        [CHEN_1976, WATT_DB_DESIGN],
    ),
    mcq(
        "db-hard-2nf-decomposition",
        ["DB-2NF", "DB-FD", "DB-NORM"],
        4,
        (
            "Relation R(student_id, course_id, student_name, course_title, "
            "grade) has primary key (student_id, course_id), with "
            "student_id -> student_name and course_id -> course_title. Which "
            "decomposition reaches 2NF and preserves both dependencies and the "
            "join?"
        ),
        [
            "student(student_id, student_name), course(course_id, "
            "course_title), enrollment(student_id, course_id, grade).",
            "student_course(student_id, course_id), names(student_id, "
            "student_name, course_title).",
            "enrollment(student_id, course_id, grade) and attributes(student_id, "
            "course_id, student_name, course_title).",
            "Keep R unchanged, because every non-key attribute depends on the "
            "whole key.",
        ],
        0,
        (
            "Both non-prime attributes depend on a proper subset of the "
            "composite key, so 2NF requires removing each partial dependency "
            "into its own relation. The enrollment relation keeps the full-key "
            "dependency grade. Joining back on student_id and course_id is "
            "lossless because each common attribute is a key of its reference "
            "relation, and all three original dependencies are enforceable "
            "inside one relation each. Option C repeats the attributes and "
            "does not normalize; option D is the original 1NF relation."
        ),
        [WATT_DB_DESIGN, CODD_1971],
    ),
    mcq(
        "db-hard-overlapping-keys-bcnf",
        ["DB-3NF", "DB-FD", "DB-NORM"],
        4,
        (
            "Relation R(Student, Course, Teacher) has functional dependencies "
            "(Student, Course) -> Teacher and Teacher -> Course. Its candidate "
            "keys are (Student, Course) and (Student, Teacher). Which statement "
            "is correct?"
        ),
        [
            "R is in 3NF but not BCNF; the BCNF decomposition into "
            "(Student, Teacher) and (Teacher, Course) is lossless but loses "
            "(Student, Course) -> Teacher.",
            "R is already in BCNF because both determinants are candidate keys.",
            "R violates 2NF because Teacher -> Course depends on part of a "
            "candidate key.",
            "The decomposition is lossy because Course appears in only one "
            "relation.",
        ],
        0,
        (
            "Teacher -> Course has a non-superkey determinant, so BCNF fails. "
            "Course is prime (it appears in the candidate key (Student, "
            "Course)), so 3NF's prime-attribute exception applies and R is in "
            "3NF. Splitting on Teacher is lossless because Teacher is a key of "
            "(Teacher, Course). The dependency (Student, Course) -> Teacher "
            "requires both Student and Course, which no single decomposed "
            "relation contains, so it is not preserved. 2NF is about partial "
            "dependencies by non-prime attributes; Course is prime."
        ),
        [WATT_DB_DESIGN, CODD_1971],
    ),
    mcq(
        "db-hard-weak-entity-key",
        ["DB-ER", "DB-NORM"],
        4,
        (
            "Payment numbers are unique only within a loan, and a payment "
            "cannot exist without its loan. Which primary-key definition "
            "correctly maps this weak entity?"
        ),
        [
            "payment(payment_id PK) with a nullable loan_id foreign key, "
            "because each payment still needs a globally unique identifier.",
            "payment(loan_id, payment_no, amount, paid_at) with primary key "
            "(loan_id, payment_no) and loan_id REFERENCES loan ON DELETE "
            "CASCADE.",
            "payment(payment_no, amount) with primary key (payment_no, amount), "
            "because the pair is unique.",
            "payment(payment_id PK, loan_id, payment_no) with a UNIQUE "
            "constraint on payment_no alone.",
        ],
        1,
        (
            "The identifying owner key loan_id plus the partial key payment_no "
            "forms the weak entity's composite primary key. The foreign key "
            "enforces existence dependence, and ON DELETE CASCADE removes "
            "payments when their loan disappears. A nullable owner key permits "
            "orphans; adding amount to the key changes identity; and uniqueness "
            "on payment_no alone contradicts the statement that numbers repeat "
            "across loans."
        ),
        [CHEN_1976, WATT_DB_DESIGN],
    ),
    mcq(
        "db-hard-prime-attribute-3nf",
        ["DB-3NF", "DB-FD", "DB-NORM"],
        5,
        (
            "Relation R(A,B,C,D) satisfies AB -> C, C -> D and D -> B. Its "
            "candidate keys are AB, AC and AD. Which statement is correct?"
        ),
        [
            "R is in BCNF because every attribute is prime.",
            "R is in 3NF but not BCNF because C -> D and D -> B have "
            "non-superkey determinants whose dependent attributes are prime.",
            "R is only in 2NF because D -> B is a partial dependency on "
            "candidate key AD.",
            "R violates 1NF because D occurs on both sides of a dependency.",
        ],
        1,
        (
            "Every attribute is prime (A, B, C and D each occur in at least one "
            "candidate key), but BCNF cares about determinants, not whether "
            "attributes are prime. C and D are not superkeys, so C -> D and "
            "D -> B violate BCNF. Because D and B are prime, 3NF's exception "
            "applies and the relation is in 3NF. 2NF is satisfied because the "
            "key is composite and no non-prime attribute depends on a proper "
            "subset; 1NF concerns atomic values."
        ),
        [WATT_DB_DESIGN, CODD_1971],
    ),
    sqlq(
        "db-hard-category-tree",
        ["DB-ER"],
        4,
        (
            "Table category(category_id INT PRIMARY KEY, name TEXT NOT NULL, "
            "parent_id INT) represents a self-referencing one-to-many "
            "relationship; NULL parent_id marks a root. Assuming no cycles, "
            "return category_id, name, depth (INT, 0 for roots) and root_name "
            "(TEXT, the name of the top-level ancestor) for every category "
            "reachable from a root. Rows whose parent chain never reaches a "
            "root are not returned. Order by depth ascending, then category_id "
            "ascending."
        ),
        (
            "WITH RECURSIVE tree AS ("
            "SELECT category_id, name, 0 AS depth, name AS root_name "
            "FROM category WHERE parent_id IS NULL "
            "UNION ALL "
            "SELECT c.category_id, c.name, t.depth + 1, t.root_name "
            "FROM category c JOIN tree t ON c.parent_id = t.category_id"
            ") SELECT category_id, name, depth, root_name FROM tree "
            "ORDER BY depth, category_id"
        ),
        [
            (
                "three_levels",
                False,
                "CREATE TABLE category(category_id INT PRIMARY KEY, name TEXT NOT NULL, parent_id INT);"
                "INSERT INTO category VALUES "
                "(1,'Electronics',NULL),(2,'Phones',1),(3,'Smartphones',2),"
                "(4,'Laptops',1),(5,'Clothing',NULL),(6,'Shirts',5);",
            ),
            (
                "roots_and_orphan",
                True,
                "CREATE TABLE category(category_id INT PRIMARY KEY, name TEXT NOT NULL, parent_id INT);"
                "INSERT INTO category VALUES "
                "(1,'Leaf',NULL),(2,'Leaf',NULL),(3,'Orphan',99);",
            ),
        ],
        (
            "The recursive term starts from roots and adds one level per "
            "iteration while carrying the root name, which implements the "
            "parent-child relationship without assuming a fixed depth. In the "
            "edge dataset the two roots are returned with the same name, which "
            "is legal because names are not keys, and the orphan whose parent "
            "does not exist is unreachable and therefore excluded. ORDER BY "
            "makes the result deterministic across executions."
        ),
        [PG_QUERIES_WITH, CHEN_1976],
    ),
    sqlq(
        "db-hard-transitive-audit",
        ["DB-NORM", "DB-FD"],
        4,
        (
            "Table employee(employee_id INT PRIMARY KEY, dept_id INT, dept_name "
            "TEXT) may contain transitive-dependency violations. Return dept_id, "
            "name_variants (BIGINT: distinct non-NULL dept_name values) and "
            "employees (BIGINT: rows in the department) for every non-NULL "
            "dept_id that has more than one distinct non-NULL dept_name. Order "
            "by name_variants descending, then dept_id ascending."
        ),
        (
            "SELECT dept_id, count(DISTINCT dept_name) AS name_variants, "
            "count(*) AS employees FROM employee WHERE dept_id IS NOT NULL "
            "GROUP BY dept_id HAVING count(DISTINCT dept_name) > 1 "
            "ORDER BY name_variants DESC, dept_id"
        ),
        [
            (
                "inconsistent_department",
                False,
                "CREATE TABLE employee(employee_id INT PRIMARY KEY, dept_id INT, dept_name TEXT);"
                "INSERT INTO employee VALUES "
                "(1,10,'Sales'),(2,10,'Sales'),(3,10,'Sales'),"
                "(4,20,'Engineering'),(5,20,'Eng'),(6,20,'Engineering'),"
                "(7,30,NULL);",
            ),
            (
                "null_only_names",
                True,
                "CREATE TABLE employee(employee_id INT PRIMARY KEY, dept_id INT, dept_name TEXT);"
                "INSERT INTO employee VALUES "
                "(1,NULL,'X'),(2,40,NULL),(3,41,NULL),(4,41,NULL);",
            ),
        ],
        (
            "If dept_id -> dept_name held, each department would have one "
            "distinct non-NULL name. The HAVING clause surfaces only departments "
            "where that is false. NULL department names are not counted as a "
            "variant, so a department with several NULLs and one real name is "
            "consistent; rows with NULL dept_id belong to no department and are "
            "excluded. The edge dataset contains no violation and returns no "
            "rows."
        ),
        [PG_AGGREGATE, WATT_DB_DESIGN],
    ),
    essay(
        "db-hard-ternary-decomposition",
        ["DB-ER", "DB-NORM", "DB-FD", "DB-3NF"],
        4,
        (
            "A supply chain records supply(supplier_id, supplier_name, "
            "supplier_city, part_id, part_name, project_id, project_name, "
            "quantity). The functional dependencies are: supplier_id -> "
            "supplier_name, supplier_city; part_id -> part_name; project_id -> "
            "project_name; and (supplier_id, part_id, project_id) -> quantity. "
            "(a) Identify the candidate key and prove it is minimal. (b) State "
            "the highest normal form and name every dependency that prevents "
            "the next form. (c) Decompose the relation into 3NF, listing "
            "primary and foreign keys. (d) Show that the decomposition is "
            "lossless-join and dependency-preserving."
        ),
        (
            "(a) The candidate key is {supplier_id, part_id, project_id}. It "
            "determines quantity directly and all descriptive attributes "
            "through the three single-attribute determinants. Removing any "
            "attribute loses the ability to distinguish supply facts for "
            "different suppliers, parts or projects, so it is minimal. "
            "(b) The highest normal form is 1NF. 2NF fails because "
            "supplier_name and supplier_city depend on supplier_id alone, "
            "part_name depends on part_id alone, and project_name depends on "
            "project_id alone; each is a proper subset of the composite key. "
            "Since 2NF fails, 3NF and BCNF are not reached. "
            "(c) supplier(supplier_id PK, supplier_name, supplier_city); "
            "part(part_id PK, part_name); "
            "project(project_id PK, project_name); "
            "supply(supplier_id PK/FK REFERENCES supplier, part_id PK/FK "
            "REFERENCES part, project_id PK/FK REFERENCES project, quantity). "
            "(d) Each partial dependency is removed by joining on a common "
            "attribute that is a key of the reference relation (supplier_id, "
            "part_id, project_id), so every split is lossless by the "
            "common-attribute test. Every functional dependency is enforced "
            "inside exactly one relation: the three descriptive dependencies in "
            "supplier, part and project, and the quantity dependency in supply. "
            "The result is also in BCNF."
        ),
        (
            "The triple is the key because quantity is meaningful only for a "
            "supplier-part-project combination. Partial dependencies on each "
            "single key attribute keep the original relation in 1NF. Splitting "
            "into supplier, part, project and supply removes them, preserves "
            "each dependency in one relation and joins back through keys, so "
            "the decomposition is both lossless and dependency-preserving."
        ),
        (
            "No candidate key or a key that omits quantity's determinant; no "
            "valid normal-form argument; the proposed decomposition loses the "
            "supply fact or cannot be joined back.",
            "Names the triple key but misses at least one partial dependency or "
            "mislabels the highest normal form; the decomposition separates "
            "some entities but keys or foreign keys are incomplete.",
            "Correct key and all four partial dependencies; decomposes into "
            "supplier, part, project and supply with keys, but the lossless or "
            "dependency-preservation argument is incomplete.",
            "Fully correct: key {supplier_id, part_id, project_id} with a "
            "minimality proof; highest form 1NF because of four partial "
            "dependencies; decomposition supplier, part, project and supply "
            "with correct primary and foreign keys; lossless by the "
            "common-attribute-key test; dependency-preserving because each "
            "dependency is enforced inside one relation.",
        ),
        [WATT_DB_DESIGN, CHEN_1976, CODD_1971],
    ),
]
