"""Security fill: privilege design, row security and defensive scenarios.

All items are MCQ or written scenarios. No item asks the learner to execute
DDL, DML, GRANT/REVOKE or a privilege-escalation attempt in the SQL sandbox.
"""

from gap_lib import essay_vi, mcq_vi
from sources import (
    PG_ALTER_DEFAULT_PRIVILEGES,
    PG_BACKUP,
    PG_CLIENT_AUTH,
    PG_CLIENT_AUTH_CH,
    PG_CONFIG,
    PG_CONSTRAINTS,
    PG_CREATE_POLICY,
    PG_PG_CLASS,
    PG_PGDUMP,
    PG_PRIV,
    PG_RLS,
    PG_ROLE_MEMBERSHIP,
    PG_ROLES,
    PG_SASL,
    PG_SCHEMA,
    PG_VIEW,
)

QUESTIONS = [
    # EASY: 6 MCQ (difficulty 2)
    mcq_vi(
        "secb-easy-public",
        ["PG-PRIVILEGE"],
        2,
        "What does GRANT SELECT ON orders TO PUBLIC mean?",
        [
            "Every role, including roles created later, can select from the table "
            "unless the privilege is revoked.",
            "Only the table owner can select from the table.",
            "Only members of a role literally named PUBLIC can select.",
            "The grant applies only to the current session.",
        ],
        0,
        (
            "PUBLIC is a pseudo-role that represents all roles. Granting a "
            "privilege to PUBLIC makes it available to every current and future "
            "role, so it is usually too broad for application tables. It is not a "
            "normal group, and it is not limited to the current session. Auditing "
            "and revoking PUBLIC grants is a core least-privilege step."
        ),
        [PG_PRIV],
        vi_prompt="GRANT SELECT ON orders TO PUBLIC có nghĩa là gì?",
        vi_options=[
            "Mọi role, kể cả role được tạo sau này, đều có thể SELECT trên bảng "
            "trừ khi quyền bị thu hồi.",
            "Chỉ chủ sở hữu bảng có thể SELECT trên bảng.",
            "Chỉ các thành viên của một role có tên đúng là PUBLIC mới có thể SELECT.",
            "Quyền chỉ có hiệu lực trong phiên hiện tại.",
        ],
        vi_explanation=(
            "PUBLIC là role giả đại diện cho mọi role. Cấp quyền cho PUBLIC khiến "
            "mọi role hiện tại và tương lai đều có quyền đó, nên thường quá rộng "
            "cho bảng ứng dụng. Đây không phải một nhóm thông thường và không giới "
            "hạn trong phiên hiện tại. Kiểm tra và thu hồi quyền PUBLIC là bước "
            "cốt lõi của nguyên tắc đặc quyền tối thiểu."
        ),
        tags=["postgresql", "security", "privileges"],
    ),
    mcq_vi(
        "secb-easy-least-privilege",
        ["PG-PRIVILEGE", "PG-ROLES"],
        2,
        "Which setup best follows least privilege for a normal application role?",
        [
            "USAGE on the application schema plus only the SELECT, INSERT, UPDATE "
            "and DELETE privileges the application needs, with no DDL or "
            "superuser rights.",
            "Superuser, so that future schema changes never need another grant.",
            "CREATEDB and CREATEROLE so the application can manage its own users.",
            "Ownership of every table so that it can alter them when needed.",
        ],
        0,
        (
            "An application role should be able to reach the schema and perform "
            "the specific data operations it needs, without owning objects or "
            "holding administrative attributes. Superuser, CREATEDB, CREATEROLE "
            "and broad ownership turn an application compromise into a "
            "database-wide compromise. Schema USAGE is required to reference "
            "objects, while CREATE on the schema is only needed for creating "
            "objects."
        ),
        [PG_PRIV, PG_ROLES],
        vi_prompt=(
            "Thiết lập nào tuân thủ nguyên tắc đặc quyền tối thiểu tốt nhất cho "
            "một role ứng dụng thông thường?"
        ),
        vi_options=[
            "USAGE trên schema ứng dụng cùng đúng các quyền SELECT, INSERT, UPDATE "
            "và DELETE mà ứng dụng cần, không có quyền DDL hay superuser.",
            "Superuser, để thay đổi schema sau này không cần cấp quyền lại.",
            "CREATEDB và CREATEROLE để ứng dụng tự quản lý người dùng của nó.",
            "Sở hữu mọi bảng để có thể sửa khi cần.",
        ],
        vi_explanation=(
            "Role ứng dụng chỉ nên truy cập được schema và thực hiện các thao tác "
            "dữ liệu cụ thể cần thiết, không sở hữu đối tượng hay giữ thuộc tính "
            "quản trị. Superuser, CREATEDB, CREATEROLE và quyền sở hữu rộng biến "
            "một sự cố ứng dụng thành sự cố toàn cơ sở dữ liệu. Cần USAGE trên "
            "schema để tham chiếu đối tượng, còn CREATE trên schema chỉ cần khi "
            "tạo đối tượng."
        ),
        tags=["postgresql", "security", "privileges"],
    ),
    mcq_vi(
        "secb-easy-schema-usage",
        ["PG-PRIVILEGE"],
        2,
        "On a schema, what is the difference between the USAGE and CREATE privileges?",
        [
            "USAGE lets a role access objects in the schema if it also has object "
            "privileges; CREATE lets it create objects in the schema.",
            "USAGE lets a role create tables; CREATE lets it read them.",
            "USAGE is only for schemas owned by the role; CREATE applies to all users.",
            "They are synonyms in PostgreSQL.",
        ],
        0,
        (
            "Schema USAGE allows a role to look up and access objects in the "
            "schema, subject to privileges on those objects. Schema CREATE allows "
            "creating new objects in it. Having USAGE does not grant table "
            "privileges, and CREATE does not imply SELECT on existing tables. Both "
            "are separate from ownership."
        ),
        [PG_PRIV, PG_SCHEMA],
        vi_prompt=(
            "Trên một schema, quyền USAGE và CREATE khác nhau như thế nào?"
        ),
        vi_options=[
            "USAGE cho phép role truy cập đối tượng trong schema nếu cũng có quyền "
            "trên đối tượng; CREATE cho phép tạo đối tượng trong schema.",
            "USAGE cho phép role tạo bảng; CREATE cho phép đọc bảng.",
            "USAGE chỉ dành cho schema do role sở hữu; CREATE áp dụng cho mọi người dùng.",
            "Chúng đồng nghĩa trong PostgreSQL.",
        ],
        vi_explanation=(
            "USAGE trên schema cho phép role tra cứu và truy cập đối tượng trong "
            "schema, tùy quyền trên các đối tượng đó. CREATE trên schema cho phép "
            "tạo đối tượng mới trong đó. Có USAGE không cấp quyền trên bảng, và "
            "CREATE không ngụ ý SELECT trên bảng hiện có. Cả hai tách biệt với quyền "
            "sở hữu."
        ),
        tags=["postgresql", "security", "privileges"],
    ),
    mcq_vi(
        "secb-easy-owner",
        ["PG-PRIVILEGE", "PG-ROLES"],
        2,
        "Who can normally ALTER or DROP a table?",
        [
            "The table owner and a superuser; a role with only SELECT cannot.",
            "Every role that can SELECT from the table.",
            "Every role that has USAGE on the schema.",
            "Only members of PUBLIC.",
        ],
        0,
        (
            "Ownership carries the right to alter and drop an object, and "
            "superusers can act as owners. Ordinary privileges such as SELECT or "
            "schema USAGE do not include DDL rights. For least privilege, "
            "application roles should not own the tables they use."
        ),
        [PG_PRIV, PG_ROLES],
        vi_prompt="Ai thông thường có thể ALTER hoặc DROP một bảng?",
        vi_options=[
            "Chủ sở hữu bảng và superuser; role chỉ có SELECT thì không.",
            "Mọi role có thể SELECT từ bảng.",
            "Mọi role có USAGE trên schema.",
            "Chỉ thành viên của PUBLIC.",
        ],
        vi_explanation=(
            "Quyền sở hữu đi kèm quyền ALTER và DROP đối tượng, và superuser có "
            "thể hành động như chủ sở hữu. Các quyền thông thường như SELECT hay "
            "USAGE trên schema không bao gồm quyền DDL. Vì đặc quyền tối thiểu, "
            "role ứng dụng không nên sở hữu các bảng mà nó dùng."
        ),
        tags=["postgresql", "security", "privileges"],
    ),
    mcq_vi(
        "secb-easy-authn-authz",
        ["PG-ROLES"],
        2,
        "What is the difference between authentication and authorization?",
        [
            "Authentication verifies who a client is; authorization decides which "
            "actions that identity may perform.",
            "Authentication decides which tables a role may read; authorization "
            "verifies the password.",
            "They are the same step, performed by GRANT.",
            "Authentication applies only to superusers; authorization applies to "
            "everyone else.",
        ],
        0,
        (
            "Authentication establishes identity, for example with a password, "
            "certificate or peer credentials. Authorization then checks the "
            "role's privileges for each action, such as SELECT on a table or "
            "CREATE on a schema. GRANT manages authorization, not authentication, "
            "and both concepts apply to ordinary roles and superusers."
        ),
        [PG_ROLES, PG_PRIV, PG_CLIENT_AUTH_CH],
        vi_prompt="Xác thực (authentication) và phân quyền (authorization) khác nhau thế nào?",
        vi_options=[
            "Xác thực kiểm tra ứng dụng là ai; phân quyền quyết định danh tính đó "
            "được thực hiện hành động nào.",
            "Xác thực quyết định role được đọc bảng nào; phân quyền kiểm tra mật khẩu.",
            "Chúng là cùng một bước, do GRANT thực hiện.",
            "Xác thực chỉ áp dụng cho superuser; phân quyền áp dụng cho mọi người khác.",
        ],
        vi_explanation=(
            "Xác thực thiết lập danh tính, ví dụ bằng mật khẩu, chứng chỉ hoặc "
            "thông tin peer. Phân quyền sau đó kiểm tra quyền của role cho từng "
            "hành động, như SELECT trên bảng hay CREATE trên schema. GRANT quản lý "
            "phân quyền, không phải xác thực, và cả hai khái niệm áp dụng cho role "
            "thông thường lẫn superuser."
        ),
        tags=["postgresql", "security", "roles"],
    ),
    mcq_vi(
        "secb-easy-set-role",
        ["PG-ROLES"],
        2,
        "What does SET ROLE analyst do in a session?",
        [
            "It switches the current role to analyst for subsequent privilege "
            "checks if the session user is a member of analyst.",
            "It changes the session user permanently and requires a new login.",
            "It grants analyst's privileges to PUBLIC.",
            "It creates the analyst role if it does not exist.",
        ],
        0,
        (
            "SET ROLE changes current_user for subsequent commands, so privilege "
            "checks use the selected role, provided the session user is a member "
            "or has been granted the role. The session user and the connection "
            "remain the same, and no role is created or granted to PUBLIC. "
            "RESET ROLE returns to the session user's default role."
        ),
        [PG_ROLE_MEMBERSHIP],
        vi_prompt="SET ROLE analyst làm gì trong một phiên?",
        vi_options=[
            "Chuyển role hiện tại sang analyst cho các kiểm tra quyền sau đó nếu "
            "người dùng phiên là thành viên của analyst.",
            "Thay đổi vĩnh viễn người dùng phiên và yêu cầu đăng nhập lại.",
            "Cấp quyền của analyst cho PUBLIC.",
            "Tạo role analyst nếu chưa tồn tại.",
        ],
        vi_explanation=(
            "SET ROLE đổi current_user cho các câu lệnh sau, nên kiểm tra quyền "
            "dùng role được chọn, miễn người dùng phiên là thành viên hoặc được cấp "
            "role đó. Người dùng phiên và kết nối không đổi, không role nào được "
            "tạo hay cấp cho PUBLIC. RESET ROLE trở về role mặc định của người dùng "
            "phiên."
        ),
        tags=["postgresql", "security", "roles"],
    ),
    # EASY: 3 essays (difficulty 2)
    essay_vi(
        "secb-easy-authorization-model",
        ["PG-ROLES", "PG-PRIVILEGE"],
        2,
        (
            "Explain PostgreSQL's authorization model: roles, role membership, "
            "object privileges, schema USAGE and ownership. How is a privilege "
            "check performed for a SELECT on a table?"
        ),
        (
            "Every login and group is a role. A session authenticates as a role, "
            "and that role's privileges, plus privileges inherited through role "
            "membership, determine what it may do. To SELECT from a table, the "
            "role needs SELECT on the table and, if the table is in a named "
            "schema, USAGE on that schema so the name can be resolved. Ownership "
            "confers implicit rights on the object, and a superuser bypasses "
            "ordinary checks. Privileges can be granted and revoked at database, "
            "schema, table, column and sequence level, and PUBLIC represents all "
            "roles. Least privilege means granting the smallest set of these "
            "rights that the workload needs."
        ),
        (
            "The answer must show that authorization combines role membership, "
            "object privileges, schema access and ownership rather than a single "
            "grant."
        ),
        [
            "Says a role only needs SELECT and ignores schema or membership.",
            "Lists roles and grants but does not trace a concrete privilege check.",
            "Traces a SELECT check through membership and schema, but omits ownership or PUBLIC.",
            "Explains roles, membership, object privileges, schema USAGE, ownership and PUBLIC, and traces a concrete SELECT check.",
        ],
        [PG_ROLES, PG_ROLE_MEMBERSHIP, PG_SCHEMA, PG_PRIV],
        vi_prompt=(
            "Hãy giải thích mô hình phân quyền của PostgreSQL: role, thành viên "
            "role, quyền trên đối tượng, USAGE trên schema và quyền sở hữu. Một "
            "kiểm tra quyền cho SELECT trên bảng diễn ra như thế nào?"
        ),
        vi_reference=(
            "Mỗi tài khoản đăng nhập và mỗi nhóm đều là một role. Phiên xác thực "
            "dưới một role, và quyền của role đó cùng quyền kế thừa qua thành viên "
            "role quyết định nó được làm gì. Để SELECT từ bảng, role cần SELECT "
            "trên bảng và, nếu bảng nằm trong schema có tên, cần USAGE trên schema "
            "để phân giải tên. Quyền sở hữu trao quyền ngầm trên đối tượng, và "
            "superuser bỏ qua các kiểm tra thông thường. Quyền có thể cấp và thu "
            "hồi ở mức cơ sở dữ liệu, schema, bảng, cột và sequence, và PUBLIC đại "
            "diện cho mọi role. Đặc quyền tối thiểu nghĩa là cấp bộ quyền nhỏ nhất "
            "mà khối công việc cần."
        ),
        vi_explanation=(
            "Câu trả lời phải cho thấy phân quyền kết hợp thành viên role, quyền "
            "trên đối tượng, quyền truy cập schema và quyền sở hữu, không chỉ một "
            "lần cấp quyền."
        ),
        vi_criteria=[
            "Cho rằng role chỉ cần SELECT và bỏ qua schema hoặc thành viên.",
            "Liệt kê role và quyền nhưng không lần theo một kiểm tra quyền cụ thể.",
            "Lần theo kiểm tra SELECT qua thành viên và schema, nhưng bỏ sót quyền sở hữu hoặc PUBLIC.",
            "Giải thích role, thành viên, quyền đối tượng, USAGE schema, quyền sở hữu và PUBLIC, đồng thời lần theo một kiểm tra SELECT cụ thể.",
        ],
        tags=["postgresql", "security", "privileges"],
    ),
    essay_vi(
        "secb-easy-default-public-risk",
        ["PG-PRIVILEGE"],
        2,
        (
            "Why are PUBLIC grants and default privileges a security risk? "
            "Describe how to audit them and how ALTER DEFAULT PRIVILEGES can make "
            "future objects safer."
        ),
        (
            "PUBLIC means every role, including roles created later, so a grant to "
            "PUBLIC on a table or function exposes it to the whole database. "
            "Defaults matter as well: PostgreSQL grants EXECUTE on functions and "
            "USAGE on types and domains to PUBLIC by default, which can expose "
            "SECURITY DEFINER routines. Auditing means checking relacl and "
            "proacl (for example through pg_class and pg_proc), "
            "information_schema.role_table_grants, role memberships and "
            "ALTER DEFAULT PRIVILEGES settings. Revoke unnecessary PUBLIC grants "
            "and set default privileges for the role that creates objects so new "
            "tables, sequences and functions start with only the intended grants. "
            "Remember that default privileges apply per creating role and can be "
            "set FOR ROLE."
        ),
        (
            "The answer must explain why PUBLIC is broad, give concrete audit "
            "sources, and show that defaults govern future objects."
        ),
        [
            "Says PUBLIC is a normal group or only recommends REVOKE without an audit.",
            "Explains the PUBLIC risk but gives no audit method or default-privilege fix.",
            "Explains the risk and an audit method, but not how defaults affect future objects.",
            "Explains PUBLIC breadth, concrete ACL audit sources and per-creator ALTER DEFAULT PRIVILEGES hardening.",
        ],
        [PG_PRIV, PG_ALTER_DEFAULT_PRIVILEGES, PG_PG_CLASS],
        vi_prompt=(
            "Vì sao quyền cho PUBLIC và quyền mặc định là rủi ro bảo mật? Hãy mô "
            "tả cách kiểm tra chúng và ALTER DEFAULT PRIVILEGES có thể làm đối "
            "tượng tương lai an toàn hơn như thế nào."
        ),
        vi_reference=(
            "PUBLIC nghĩa là mọi role, kể cả role được tạo sau, nên cấp quyền cho "
            "PUBLIC trên bảng hoặc hàm phơi bày đối tượng đó cho toàn cơ sở dữ "
            "liệu. Quyền mặc định cũng quan trọng: PostgreSQL mặc định cấp EXECUTE "
            "trên hàm và USAGE trên kiểu và domain cho PUBLIC, có thể phơi bày các "
            "routine SECURITY DEFINER. Kiểm tra nghĩa là xem relacl và proacl (ví "
            "dụ qua pg_class và pg_proc), "
            "information_schema.role_table_grants, thành viên role và cấu hình "
            "ALTER DEFAULT PRIVILEGES. Thu hồi quyền PUBLIC không cần thiết và đặt "
            "quyền mặc định cho role tạo đối tượng để bảng, sequence và hàm mới "
            "chỉ có quyền dự định. Lưu ý quyền mặc định áp dụng theo role tạo và có "
            "thể đặt FOR ROLE."
        ),
        vi_explanation=(
            "Câu trả lời phải giải thích vì sao PUBLIC rộng, nêu nguồn kiểm tra cụ "
            "thể, và cho thấy quyền mặc định chi phối đối tượng tương lai."
        ),
        vi_criteria=[
            "Cho rằng PUBLIC là nhóm thông thường hoặc chỉ khuyên REVOKE mà không có cách kiểm tra.",
            "Giải thích rủi ro PUBLIC nhưng không nêu cách kiểm tra hoặc cách sửa bằng quyền mặc định.",
            "Giải thích rủi ro và cách kiểm tra, nhưng không nêu quyền mặc định ảnh hưởng đối tượng tương lai thế nào.",
            "Giải thích độ rộng của PUBLIC, nguồn kiểm tra ACL cụ thể và cách siết quyền mặc định theo role tạo bằng ALTER DEFAULT PRIVILEGES.",
        ],
        tags=["postgresql", "security", "privileges"],
    ),
    essay_vi(
        "secb-easy-rls-intro",
        ["PG-RLS"],
        2,
        (
            "Explain row-level security at an introductory level: enabling it, "
            "defining policies, USING versus WITH CHECK, and who bypasses it by "
            "default. Why does enabling RLS without a policy deny access?"
        ),
        (
            "After ALTER TABLE ... ENABLE ROW LEVEL SECURITY, a table with no "
            "policies has a default-deny behaviour for ordinary users: no rows are "
            "visible and no rows may be written. A policy attaches an expression "
            "to a command. For SELECT, UPDATE and DELETE, USING controls which "
            "existing rows the role may see or target. For INSERT and UPDATE, WITH "
            "CHECK controls which new row versions may be written. Permissive "
            "policies are combined with OR, while restrictive policies are "
            "combined with AND. The table owner normally bypasses RLS, and "
            "superusers or roles with BYPASSRLS always do; FORCE ROW LEVEL "
            "SECURITY makes owner queries subject to policies too. RLS filters "
            "rows, so it complements rather than replaces table privileges."
        ),
        (
            "The answer must distinguish USING from WITH CHECK, explain default "
            "deny and name the normal bypass cases."
        ),
        [
            "Says RLS hides columns or that enabling it grants access automatically.",
            "Explains policies but confuses USING with WITH CHECK or omits owner bypass.",
            "Explains enabling, USING, WITH CHECK and default deny, but omits FORCE or superuser bypass.",
            "Explains enabling, default deny, USING versus WITH CHECK, owner and superuser bypass and FORCE RLS.",
        ],
        [PG_RLS, PG_PRIV, PG_CREATE_POLICY],
        vi_prompt=(
            "Hãy giải thích row-level security ở mức nhập môn: bật nó, định nghĩa "
            "policy, USING so với WITH CHECK, và ai mặc định bỏ qua nó. Vì sao bật "
            "RLS mà không có policy lại từ chối truy cập?"
        ),
        vi_reference=(
            "Sau ALTER TABLE ... ENABLE ROW LEVEL SECURITY, bảng không có policy "
            "có hành vi từ chối mặc định với người dùng thông thường: không dòng "
            "nào hiển thị và không dòng nào được ghi. Policy gắn biểu thức vào một "
            "lệnh. Với SELECT, UPDATE và DELETE, USING kiểm soát các dòng hiện có "
            "mà role được thấy hoặc nhắm tới. Với INSERT và UPDATE, WITH CHECK "
            "kiểm soát phiên bản dòng mới được ghi. Policy permissive kết hợp bằng "
            "OR, còn restrictive kết hợp bằng AND. Chủ sở hữu bảng mặc định bỏ qua "
            "RLS, superuser hoặc role có BYPASSRLS luôn bỏ qua; FORCE ROW LEVEL "
            "SECURITY khiến truy vấn của chủ sở hữu cũng chịu policy. RLS lọc dòng, "
            "nên bổ sung chứ không thay thế quyền trên bảng."
        ),
        vi_explanation=(
            "Câu trả lời phải phân biệt USING với WITH CHECK, giải thích từ chối "
            "mặc định và nêu các trường hợp bỏ qua thông thường."
        ),
        vi_criteria=[
            "Cho rằng RLS ẩn cột hoặc bật RLS tự động cấp quyền truy cập.",
            "Giải thích policy nhưng nhầm USING với WITH CHECK hoặc bỏ sót chủ sở hữu bỏ qua.",
            "Giải thích bật RLS, USING, WITH CHECK và từ chối mặc định, nhưng bỏ sót FORCE hoặc superuser bỏ qua.",
            "Giải thích bật RLS, từ chối mặc định, USING so với WITH CHECK, chủ sở hữu và superuser bỏ qua, và FORCE RLS.",
        ],
        tags=["postgresql", "security", "rls"],
    ),
    # MEDIUM: 3 MCQ (difficulty 3)
    mcq_vi(
        "secb-medium-noinherit",
        ["PG-ROLES"],
        3,
        (
            "A login role is a member of reporting but was granted membership with "
            "INHERIT FALSE. What must it do to use reporting's privileges?"
        ),
        [
            "Run SET ROLE reporting (or use a role whose membership inherits) "
            "before performing the action.",
            "Nothing: membership always applies immediately.",
            "Ask for a new grant to PUBLIC.",
            "Restart the PostgreSQL server.",
        ],
        0,
        (
            "INHERIT FALSE, or a member role with NOINHERIT, means the member does "
            "not automatically use the granted role's privileges. It must switch "
            "with SET ROLE, provided it has membership, and RESET ROLE afterwards. "
            "Membership does not become a PUBLIC grant, and no restart is needed."
        ),
        [PG_ROLE_MEMBERSHIP, PG_ROLES],
        vi_prompt=(
            "Một role đăng nhập là thành viên của reporting nhưng được cấp thành "
            "viên với INHERIT FALSE. Role này phải làm gì để dùng quyền của "
            "reporting?"
        ),
        vi_options=[
            "Chạy SET ROLE reporting (hoặc dùng role có thành viên kế thừa) trước "
            "khi thực hiện hành động.",
            "Không cần làm gì: thành viên luôn áp dụng ngay.",
            "Yêu cầu cấp quyền mới cho PUBLIC.",
            "Khởi động lại máy chủ PostgreSQL.",
        ],
        vi_explanation=(
            "INHERIT FALSE, hoặc role thành viên có NOINHERIT, nghĩa là thành viên "
            "không tự động dùng quyền của role được cấp. Nó phải chuyển bằng SET "
            "ROLE, miễn có thành viên, và RESET ROLE sau đó. Thành viên không trở "
            "thành quyền cho PUBLIC, và không cần khởi động lại."
        ),
        tags=["postgresql", "security", "roles"],
    ),
    mcq_vi(
        "secb-medium-sequence-usage",
        ["PG-PRIVILEGE"],
        3,
        (
            "A table has a serial column whose default calls nextval on a separate "
            "sequence. An application role has INSERT on the table but no privilege "
            "on the sequence. What happens on INSERT?"
        ),
        [
            "The insert fails because the role also needs USAGE (or UPDATE) on the "
            "sequence.",
            "The insert succeeds because table INSERT implies all default privileges.",
            "The insert succeeds but the sequence value is not incremented.",
            "The insert fails only when the sequence reaches its maximum.",
        ],
        0,
        (
            "A serial column is a separate sequence object, and evaluating its "
            "default requires sequence access. The application role needs USAGE or "
            "UPDATE on the sequence in addition to INSERT on the table. Table "
            "INSERT does not imply sequence privileges, and the failure happens "
            "immediately rather than at sequence exhaustion."
        ),
        [PG_PRIV],
        vi_prompt=(
            "Một bảng có cột serial với giá trị mặc định gọi nextval trên một "
            "sequence riêng. Role ứng dụng có INSERT trên bảng nhưng không có "
            "quyền trên sequence. Điều gì xảy ra khi INSERT?"
        ),
        vi_options=[
            "Lệnh chèn thất bại vì role cũng cần USAGE (hoặc UPDATE) trên sequence.",
            "Lệnh chèn thành công vì INSERT trên bảng ngụ ý mọi quyền mặc định.",
            "Lệnh chèn thành công nhưng giá trị sequence không tăng.",
            "Lệnh chèn chỉ thất bại khi sequence đạt giá trị tối đa.",
        ],
        vi_explanation=(
            "Cột serial là một đối tượng sequence riêng, và việc đánh giá giá trị "
            "mặc định cần quyền truy cập sequence. Role ứng dụng cần USAGE hoặc "
            "UPDATE trên sequence ngoài INSERT trên bảng. INSERT trên bảng không "
            "ngụ ý quyền sequence, và lỗi xảy ra ngay chứ không phải khi sequence "
            "cạn."
        ),
        tags=["postgresql", "security", "privileges"],
    ),
    mcq_vi(
        "secb-medium-column-vs-view",
        ["PG-PRIVILEGE", "PG-RLS"],
        3,
        (
            "A role must see only the name and department columns of employees and "
            "only rows for its own department. Which design fits best?"
        ),
        [
            "A view that selects the allowed columns and filters by department, "
            "with privileges on the view; or column grants plus an RLS policy.",
            "GRANT SELECT (name, department) alone, because column privileges also "
            "filter rows.",
            "GRANT SELECT ON employees, because the application can hide columns "
            "in its UI.",
            "A UNIQUE index on department.",
        ],
        0,
        (
            "Column privileges restrict which columns can be read but do not filter "
            "rows, so they are insufficient for the row requirement by themselves. "
            "A view can project the allowed columns and apply a row filter, and the "
            "role is granted access to the view rather than the base table; a "
            "security barrier or SECURITY DEFINER view must be designed carefully. "
            "Alternatively, column grants plus an RLS policy handle columns and "
            "rows separately. UI hiding is not a database control, and an index "
            "does not restrict access."
        ),
        [PG_PRIV, PG_RLS, PG_VIEW],
        vi_prompt=(
            "Một role chỉ được thấy các cột name và department của bảng employees "
            "và chỉ các dòng thuộc phòng ban của nó. Thiết kế nào phù hợp nhất?"
        ),
        vi_options=[
            "Một view chọn các cột được phép và lọc theo phòng ban, cấp quyền trên "
            "view; hoặc cấp quyền theo cột kèm policy RLS.",
            "Chỉ GRANT SELECT (name, department), vì quyền theo cột cũng lọc dòng.",
            "GRANT SELECT ON employees, vì ứng dụng có thể ẩn cột trên giao diện.",
            "Một chỉ mục UNIQUE trên department.",
        ],
        vi_explanation=(
            "Quyền theo cột giới hạn cột được đọc nhưng không lọc dòng, nên tự nó "
            "không đủ cho yêu cầu về dòng. View có thể chiếu các cột được phép và "
            "áp bộ lọc dòng, và role được cấp quyền trên view thay vì bảng gốc; "
            "view security barrier hoặc SECURITY DEFINER phải được thiết kế cẩn "
            "thận. Cách khác là cấp quyền theo cột kèm policy RLS để xử lý cột và "
            "dòng riêng. Ẩn trên giao diện không phải kiểm soát cơ sở dữ liệu, và "
            "chỉ mục không hạn chế truy cập."
        ),
        tags=["postgresql", "security", "privileges"],
    ),
    # MEDIUM: 2 essays (difficulty 3)
    essay_vi(
        "secb-medium-injection-blast-radius",
        ["PG-PRIVILEGE", "PG-RLS"],
        3,
        (
            "An application builds SQL by concatenating user input. Explain how "
            "parameterized queries prevent injection, and how least privilege and "
            "RLS limit the blast radius if a defect still allows injected SQL. "
            "Mention one danger of SECURITY DEFINER and one of dynamic SQL."
        ),
        (
            "Parameterized queries send SQL text and values separately, so input "
            "is treated as data and cannot change the statement's structure. "
            "String concatenation lets an attacker terminate a literal and add "
            "clauses, UNIONs or stacked statements, so prevention is the first "
            "control. If a defect remains, least privilege limits what the "
            "application role can read or change; RLS can restrict rows even when "
            "the role can run a query. A SECURITY DEFINER function runs with the "
            "owner's privileges and can bypass the caller's restrictions if it is "
            "carelessly written, especially with an unsafe search_path. Dynamic SQL "
            "inside functions or procedures must use parameters (for example "
            "EXECUTE ... USING) and quote identifiers with format/quote_ident, or "
            "it reintroduces injection."
        ),
        (
            "The answer must separate prevention (parameters) from containment "
            "(privileges, RLS) and give one concrete definer or dynamic-SQL risk."
        ),
        [
            "Recommends only escaping quotes or hiding errors, with no parameterization.",
            "Explains parameterization but not least privilege or RLS containment.",
            "Explains prevention and containment, but omits definer or dynamic-SQL risk.",
            "Explains parameterization, privilege and RLS containment, and a concrete SECURITY DEFINER or dynamic-SQL danger.",
        ],
        [PG_PRIV, PG_RLS],
        vi_prompt=(
            "Một ứng dụng xây SQL bằng cách nối chuỗi đầu vào người dùng. Hãy giải "
            "thích truy vấn tham số hóa ngăn injection thế nào, và đặc quyền tối "
            "thiểu cùng RLS giới hạn phạm vi thiệt hại ra sao nếu lỗi vẫn cho phép "
            "SQL bị chèn. Nêu một nguy hiểm của SECURITY DEFINER và một của SQL "
            "động."
        ),
        vi_reference=(
            "Truy vấn tham số hóa gửi văn bản SQL và giá trị riêng, nên đầu vào "
            "được xử lý như dữ liệu và không thể thay đổi cấu trúc câu lệnh. Nối "
            "chuỗi cho phép kẻ tấn công kết thúc literal và thêm mệnh đề, UNION "
            "hoặc nhiều câu lệnh, nên phòng ngừa là kiểm soát đầu tiên. Nếu vẫn "
            "còn lỗi, đặc quyền tối thiểu giới hạn thứ ứng dụng có thể đọc hoặc "
            "sửa; RLS có thể giới hạn dòng ngay cả khi role chạy được truy vấn. Hàm "
            "SECURITY DEFINER chạy với quyền của chủ sở hữu và có thể bỏ qua hạn "
            "chế của người gọi nếu viết cẩu thả, đặc biệt với search_path không an "
            "toàn. SQL động trong hàm hoặc thủ tục phải dùng tham số (ví dụ EXECUTE "
            "... USING) và trích dẫn định danh bằng format/quote_ident, nếu không "
            "sẽ tái tạo lỗ hổng injection."
        ),
        vi_explanation=(
            "Câu trả lời phải tách phòng ngừa (tham số) khỏi giới hạn thiệt hại "
            "(quyền, RLS) và nêu một rủi ro cụ thể của definer hoặc SQL động."
        ),
        vi_criteria=[
            "Chỉ khuyên thoát dấu nháy hoặc ẩn lỗi, không có tham số hóa.",
            "Giải thích tham số hóa nhưng không nêu đặc quyền tối thiểu hoặc RLS để giới hạn thiệt hại.",
            "Giải thích phòng ngừa và giới hạn thiệt hại, nhưng bỏ sót rủi ro definer hoặc SQL động.",
            "Giải thích tham số hóa, giới hạn bằng quyền và RLS, và một nguy hiểm cụ thể của SECURITY DEFINER hoặc SQL động.",
        ],
        tags=["postgresql", "security", "injection"],
    ),
    essay_vi(
        "secb-medium-privilege-audit",
        ["PG-PRIVILEGE", "PG-ROLES"],
        3,
        (
            "Design a privilege audit for an existing PostgreSQL database. What "
            "would you inspect for roles, memberships, table and schema grants, "
            "sequences, default ACLs, row security and unused accounts? What would "
            "you report and remediate?"
        ),
        (
            "Start with roles and attributes: superuser, CREATEDB, CREATEROLE, "
            "REPLICATION, BYPASSRLS, LOGIN and password validity, plus role "
            "memberships that may cascade privileges. Inspect schema USAGE and "
            "CREATE grants, table ACLs (relacl), column grants, sequence grants, "
            "function EXECUTE grants and default ACLs for future objects, "
            "including PUBLIC entries. Check which tables have RLS enabled, which "
            "have FORCE, and which policies exist; a table with RLS enabled and no "
            "policy is default-deny. Review ownership so application roles do not "
            "own production objects. Identify unused or shared accounts and stale "
            "grants, then remediate by revoking unnecessary PUBLIC and group "
            "grants, separating migration and runtime roles, setting default "
            "privileges, and re-testing the application. Report findings by "
            "object, grantee, privilege source and risk, with an owner and a "
            "deadline."
        ),
        (
            "The answer must cover more than table grants: roles, memberships, "
            "sequences, defaults, RLS, ownership and unused accounts, plus a "
            "remediation plan."
        ),
        [
            "Only lists table SELECT grants and REVOKE ALL.",
            "Covers tables and roles but omits sequences, defaults, RLS or ownership.",
            "Covers most areas and some remediation, but lacks a concrete report or follow-up.",
            "Covers roles, memberships, schema, table, column, sequence, defaults, RLS, ownership and unused accounts, with a prioritized remediation and re-test.",
        ],
        [PG_PRIV, PG_PG_CLASS, PG_ROLES, PG_ROLE_MEMBERSHIP, PG_RLS],
        vi_prompt=(
            "Hãy thiết kế một cuộc kiểm tra quyền cho một cơ sở dữ liệu PostgreSQL "
            "hiện có. Bạn sẽ xem xét gì về role, thành viên, quyền trên bảng và "
            "schema, sequence, ACL mặc định, bảo mật dòng và tài khoản không dùng? "
            "Bạn sẽ báo cáo và khắc phục những gì?"
        ),
        vi_reference=(
            "Bắt đầu với role và thuộc tính: superuser, CREATEDB, CREATEROLE, "
            "REPLICATION, BYPASSRLS, LOGIN và hiệu lực mật khẩu, cùng thành viên "
            "role có thể lan truyền quyền. Xem USAGE và CREATE trên schema, ACL "
            "bảng (relacl), quyền theo cột, quyền sequence, EXECUTE trên hàm và ACL "
            "mặc định cho đối tượng tương lai, gồm các mục PUBLIC. Kiểm tra bảng "
            "nào bật RLS, bảng nào có FORCE và policy nào tồn tại; bảng bật RLS mà "
            "không có policy là từ chối mặc định. Rà quyền sở hữu để role ứng dụng "
            "không sở hữu đối tượng sản xuất. Xác định tài khoản không dùng hoặc "
            "dùng chung và quyền cũ, rồi khắc phục bằng cách thu hồi quyền PUBLIC "
            "và nhóm không cần thiết, tách role migration khỏi role runtime, đặt "
            "quyền mặc định và kiểm thử lại ứng dụng. Báo cáo theo đối tượng, người "
            "được cấp, nguồn quyền và rủi ro, kèm người phụ trách và hạn chót."
        ),
        vi_explanation=(
            "Câu trả lời phải bao quát hơn quyền trên bảng: role, thành viên, "
            "sequence, quyền mặc định, RLS, quyền sở hữu và tài khoản không dùng, "
            "cùng kế hoạch khắc phục."
        ),
        vi_criteria=[
            "Chỉ liệt kê quyền SELECT trên bảng và REVOKE ALL.",
            "Bao quát bảng và role nhưng bỏ sót sequence, quyền mặc định, RLS hoặc quyền sở hữu.",
            "Bao quát phần lớn lĩnh vực và một số biện pháp khắc phục, nhưng thiếu báo cáo cụ thể hoặc bước theo dõi.",
            "Bao quát role, thành viên, schema, bảng, cột, sequence, quyền mặc định, RLS, quyền sở hữu và tài khoản không dùng, cùng khắc phục ưu tiên và kiểm thử lại.",
        ],
        tags=["postgresql", "security", "audit"],
    ),
    # HARD: 6 MCQ (difficulty 4)
    mcq_vi(
        "secb-hard-force-rls",
        ["PG-RLS"],
        4,
        (
            "A table owner enables row-level security and defines policies, but "
            "queries run by the owner still see all rows. What explains this, and "
            "what changes it?"
        ),
        [
            "Table owners bypass RLS unless FORCE ROW LEVEL SECURITY is enabled; "
            "superusers and BYPASSRLS roles always bypass.",
            "The policies are invalid because the owner did not grant SELECT to "
            "PUBLIC.",
            "RLS never applies to SELECT, only to INSERT and DELETE.",
            "The owner must reconnect before RLS policies take effect.",
        ],
        0,
        (
            "By default the owner of a table is not subject to its row security "
            "policies, and superusers or roles with BYPASSRLS always bypass them. "
            "ALTER TABLE ... FORCE ROW LEVEL SECURITY makes owner queries subject "
            "to policies, but it still does not restrict superusers or BYPASSRLS. "
            "RLS applies to SELECT as well as writes, and reconnecting is not the "
            "mechanism. For a genuine test, query as a non-owner role without "
            "BYPASSRLS."
        ),
        [PG_RLS, PG_ROLES],
        vi_prompt=(
            "Chủ sở hữu bảng bật row-level security và định nghĩa policy, nhưng "
            "truy vấn do chủ sở hữu chạy vẫn thấy mọi dòng. Điều gì giải thích, và "
            "thay đổi gì khắc phục?"
        ),
        vi_options=[
            "Chủ sở hữu bảng bỏ qua RLS trừ khi bật FORCE ROW LEVEL SECURITY; "
            "superuser và role BYPASSRLS luôn bỏ qua.",
            "Policy không hợp lệ vì chủ sở hữu chưa cấp SELECT cho PUBLIC.",
            "RLS không bao giờ áp dụng cho SELECT, chỉ cho INSERT và DELETE.",
            "Chủ sở hữu phải kết nối lại trước khi policy RLS có hiệu lực.",
        ],
        vi_explanation=(
            "Mặc định chủ sở hữu bảng không chịu policy bảo mật dòng, và superuser "
            "hoặc role có BYPASSRLS luôn bỏ qua. ALTER TABLE ... FORCE ROW LEVEL "
            "SECURITY khiến truy vấn của chủ sở hữu chịu policy, nhưng vẫn không "
            "hạn chế superuser hay BYPASSRLS. RLS áp dụng cho SELECT cũng như ghi, "
            "và kết nối lại không phải cơ chế. Để kiểm tra thực, hãy truy vấn bằng "
            "role không phải chủ sở hữu và không có BYPASSRLS."
        ),
        tags=["postgresql", "security", "rls"],
    ),
    mcq_vi(
        "secb-hard-policy-function",
        ["PG-RLS", "PG-PRIVILEGE"],
        4,
        (
            "A row security policy calls a user-defined function. Which risk "
            "matters most?"
        ),
        [
            "If the function is SECURITY DEFINER, it can read or expose rows "
            "beyond the caller's rights; policy functions must be audited and kept "
            "minimal.",
            "PostgreSQL refuses to evaluate user-defined functions in policies.",
            "Marking a function LEAKPROOF automatically applies RLS inside it.",
            "Policies always run as the table owner, so every policy function sees "
            "all rows.",
        ],
        0,
        (
            "A policy expression is evaluated as part of the query and can call "
            "functions. A SECURITY DEFINER function runs with its owner's rights, "
            "so it can bypass the caller's restrictions if it reads protected "
            "tables or returns too much data; keep policy functions simple, owned "
            "by a trusted role, and with a safe search_path. PostgreSQL does "
            "evaluate user-defined functions in policies, LEAKPROOF is a planner "
            "property and not an RLS switch, and policies do not automatically run "
            "as the table owner."
        ),
        [PG_RLS, PG_PRIV],
        vi_prompt=(
            "Một policy bảo mật dòng gọi hàm do người dùng định nghĩa. Rủi ro nào "
            "quan trọng nhất?"
        ),
        vi_options=[
            "Nếu hàm là SECURITY DEFINER, nó có thể đọc hoặc để lộ dòng ngoài quyền "
            "của người gọi; hàm trong policy phải được kiểm tra và giữ tối giản.",
            "PostgreSQL từ chối đánh giá hàm do người dùng định nghĩa trong policy.",
            "Đánh dấu hàm LEAKPROOF tự động áp dụng RLS bên trong nó.",
            "Policy luôn chạy dưới quyền chủ sở hữu bảng, nên mọi hàm trong policy "
            "thấy mọi dòng.",
        ],
        vi_explanation=(
            "Biểu thức policy được đánh giá như một phần của truy vấn và có thể gọi "
            "hàm. Hàm SECURITY DEFINER chạy với quyền chủ sở hữu, nên có thể bỏ qua "
            "hạn chế của người gọi nếu đọc bảng được bảo vệ hoặc trả về quá nhiều "
            "dữ liệu; hãy giữ hàm trong policy đơn giản, do role tin cậy sở hữu và "
            "có search_path an toàn. PostgreSQL có đánh giá hàm do người dùng định "
            "nghĩa trong policy, LEAKPROOF là thuộc tính cho bộ lập kế hoạch chứ "
            "không phải công tắc RLS, và policy không tự động chạy dưới quyền chủ "
            "sở hữu bảng."
        ),
        tags=["postgresql", "security", "rls"],
    ),
    mcq_vi(
        "secb-hard-policy-subquery",
        ["PG-RLS"],
        4,
        (
            "An RLS policy on orders contains a subquery against accounts. Which "
            "statement is correct?"
        ),
        [
            "The subquery runs as part of the caller's query, so the accounts "
            "policies and privileges also apply; this can add cost and unexpected "
            "empty results.",
            "The subquery always bypasses accounts RLS because it appears inside a "
            "policy.",
            "A policy may not reference another table, so the policy is rejected.",
            "The subquery runs as the table owner and therefore sees every account.",
        ],
        0,
        (
            "Policy expressions are part of the query, and a subquery against "
            "another table is subject to that table's row security and the "
            "caller's privileges. The result can be fewer rows than expected or "
            "extra planning and execution cost. Policies may reference other "
            "tables, and they do not gain owner rights just by being policies. "
            "Design policies to be simple and indexed, and test with the actual "
            "application roles."
        ),
        [PG_RLS, PG_PRIV],
        vi_prompt=(
            "Một policy RLS trên orders chứa truy vấn con tới accounts. Phát biểu "
            "nào đúng?"
        ),
        vi_options=[
            "Truy vấn con chạy như một phần truy vấn của người gọi, nên policy và "
            "quyền trên accounts cũng áp dụng; điều này có thể tăng chi phí và gây "
            "kết quả rỗng bất ngờ.",
            "Truy vấn con luôn bỏ qua RLS của accounts vì nó nằm trong policy.",
            "Policy không được tham chiếu bảng khác nên policy bị từ chối.",
            "Truy vấn con chạy dưới quyền chủ sở hữu bảng nên thấy mọi tài khoản.",
        ],
        vi_explanation=(
            "Biểu thức policy là một phần của truy vấn, và truy vấn con tới bảng "
            "khác chịu bảo mật dòng cùng quyền của người gọi trên bảng đó. Kết quả "
            "có thể ít dòng hơn dự kiến hoặc tốn thêm chi phí lập và thực thi kế "
            "hoạch. Policy được phép tham chiếu bảng khác và không tự có quyền chủ "
            "sở hữu chỉ vì là policy. Hãy thiết kế policy đơn giản, có chỉ mục và "
            "kiểm thử với role ứng dụng thực tế."
        ),
        tags=["postgresql", "security", "rls"],
    ),
    mcq_vi(
        "secb-hard-dump-acl",
        ["PG-BACKUP", "PG-PRIVILEGE"],
        4,
        (
            "A non-superuser restores a pg_dump into a new database and finds "
            "ownership errors and missing grants. What is the safest explanation "
            "and response?"
        ),
        [
            "The dump contains ownership and ACL commands the restoring role "
            "cannot apply; restore with --no-owner --no-privileges and grant "
            "privileges deliberately afterwards.",
            "pg_dump never includes ACLs, so the missing grants are unrelated.",
            "The restore should be run as the original table owner's password "
            "without any options.",
            "The errors can be ignored because PostgreSQL applies default "
            "privileges automatically to restored tables.",
        ],
        0,
        (
            "A plain or custom pg_dump can include ALTER ... OWNER and GRANT/REVOKE "
            "commands. A non-superuser may not be able to set ownership to the "
            "original roles or grant privileges it does not hold, producing errors "
            "or a partially restored security model. --no-owner and "
            "--no-privileges skip those commands so the restoring role owns the "
            "objects and can apply a reviewed privilege plan. Default privileges "
            "do not retroactively fix restored tables, and ignoring the errors can "
            "leave a database with the wrong exposure."
        ),
        [PG_BACKUP, PG_PGDUMP, PG_PRIV],
        vi_prompt=(
            "Một người dùng không phải superuser phục hồi pg_dump vào cơ sở dữ liệu "
            "mới và gặp lỗi quyền sở hữu cùng thiếu quyền. Cách giải thích và phản "
            "ứng an toàn nhất là gì?"
        ),
        vi_options=[
            "Bản dump chứa lệnh chủ sở hữu và ACL mà role phục hồi không áp dụng "
            "được; hãy phục hồi với --no-owner --no-privileges rồi cấp quyền có chủ "
            "đích sau.",
            "pg_dump không bao giờ chứa ACL, nên quyền thiếu không liên quan.",
            "Nên chạy phục hồi bằng mật khẩu của chủ sở hữu bảng gốc mà không cần "
            "tùy chọn nào.",
            "Có thể bỏ qua lỗi vì PostgreSQL tự áp quyền mặc định cho bảng được "
            "phục hồi.",
        ],
        vi_explanation=(
            "pg_dump dạng plain hoặc custom có thể chứa lệnh ALTER ... OWNER và "
            "GRANT/REVOKE. Người dùng không phải superuser có thể không đặt được "
            "chủ sở hữu là role gốc hoặc không cấp được quyền mình không có, gây "
            "lỗi hoặc mô hình bảo mật phục hồi dở dang. --no-owner và "
            "--no-privileges bỏ qua các lệnh đó để role phục hồi sở hữu đối tượng "
            "và áp kế hoạch quyền đã được duyệt. Quyền mặc định không sửa hồi tố "
            "bảng đã phục hồi, và bỏ qua lỗi có thể để lại cơ sở dữ liệu phơi bày "
            "sai."
        ),
        tags=["postgresql", "security", "backup"],
    ),
    mcq_vi(
        "secb-hard-scram-binding",
        ["PG-ROLES", "PG-PRIVILEGE"],
        4,
        (
            "What does SCRAM-SHA-256-PLUS add over SCRAM-SHA-256 for PostgreSQL "
            "password authentication?"
        ),
        [
            "Channel binding ties the authentication exchange to the TLS "
            "connection, helping detect a man-in-the-middle that terminates TLS.",
            "It stores passwords in plaintext so the server can compare them "
            "directly.",
            "It removes the need for TLS by encrypting the whole session.",
            "It lets any role log in without a password once the password is set.",
        ],
        0,
        (
            "SCRAM-SHA-256-PLUS uses channel binding so the client and server can "
            "verify that they are talking over the same TLS connection, which "
            "raises the bar for a man-in-the-middle that proxies TLS. It still uses "
            "a salted password verifier, does not encrypt the whole session by "
            "itself, and does not remove authentication. It requires TLS and client "
            "support; password_encryption controls the stored verifier format, not "
            "authorization."
        ),
        [PG_CLIENT_AUTH, PG_SASL],
        vi_prompt=(
            "SCRAM-SHA-256-PLUS bổ sung gì so với SCRAM-SHA-256 cho xác thực mật "
            "khẩu PostgreSQL?"
        ),
        vi_options=[
            "Channel binding gắn trao đổi xác thực với kết nối TLS, giúp phát hiện "
            "kẻ đứng giữa chấm dứt TLS.",
            "Nó lưu mật khẩu dạng văn bản thuần để máy chủ so sánh trực tiếp.",
            "Nó loại bỏ nhu cầu TLS bằng cách mã hóa toàn bộ phiên.",
            "Nó cho phép mọi role đăng nhập không cần mật khẩu sau khi đặt mật khẩu.",
        ],
        vi_explanation=(
            "SCRAM-SHA-256-PLUS dùng channel binding để máy khách và máy chủ xác "
            "minh đang nói chuyện trên cùng kết nối TLS, nâng cao rào cản với kẻ "
            "đứng giữa proxy TLS. Nó vẫn dùng bộ xác minh mật khẩu có muối, không tự "
            "mã hóa toàn phiên và không loại bỏ xác thực. Nó cần TLS và hỗ trợ phía "
            "máy khách; password_encryption điều khiển định dạng bộ xác minh lưu "
            "trữ, không phải phân quyền."
        ),
        tags=["postgresql", "security", "authentication"],
    ),
    mcq_vi(
        "secb-hard-ri-bypass-rls",
        ["PG-RLS"],
        4,
        (
            "A table uses RLS to hide rows from a tenant. A unique constraint or "
            "foreign key check needs to inspect rows the tenant cannot see. Which "
            "statement is correct?"
        ),
        [
            "Constraint checks bypass row security to preserve integrity, so "
            "uniqueness or references can reveal that a hidden value exists; do not "
            "rely on RLS to hide keys from constraint errors.",
            "RLS always applies to constraint checks, so uniqueness is only "
            "enforced within visible rows.",
            "Foreign keys are disabled automatically when RLS is enabled.",
            "Constraint checks see only rows owned by the current role.",
        ],
        0,
        (
            "Referential integrity and uniqueness checks are performed against the "
            "whole table and bypass RLS, because otherwise integrity could depend "
            "on who is writing. That means a duplicate-key or foreign-key error can "
            "reveal that a hidden value exists. Use opaque keys, avoid exposing "
            "constraint details in errors, and treat RLS as row visibility for "
            "queries rather than a mechanism for hiding the existence of keys."
        ),
        [PG_RLS, PG_CONSTRAINTS],
        vi_prompt=(
            "Một bảng dùng RLS để ẩn dòng giữa các tenant. Kiểm tra ràng buộc duy "
            "nhất hoặc khóa ngoại cần xem các dòng mà tenant không thấy. Phát biểu "
            "nào đúng?"
        ),
        vi_options=[
            "Kiểm tra ràng buộc bỏ qua bảo mật dòng để bảo toàn toàn vẹn, nên lỗi "
            "duy nhất hoặc khóa ngoại có thể tiết lộ giá trị ẩn tồn tại; đừng dựa "
            "vào RLS để ẩn khóa khỏi lỗi ràng buộc.",
            "RLS luôn áp dụng cho kiểm tra ràng buộc, nên tính duy nhất chỉ được "
            "thực thi trong các dòng hiển thị.",
            "Khóa ngoại tự động bị vô hiệu hóa khi bật RLS.",
            "Kiểm tra ràng buộc chỉ thấy các dòng do role hiện tại sở hữu.",
        ],
        vi_explanation=(
            "Kiểm tra toàn vẹn tham chiếu và duy nhất được thực hiện trên toàn bảng "
            "và bỏ qua RLS, vì nếu không tính toàn vẹn sẽ phụ thuộc vào người ghi. "
            "Điều đó nghĩa là lỗi trùng khóa hoặc khóa ngoại có thể tiết lộ giá trị "
            "ẩn tồn tại. Hãy dùng khóa khó đoán, tránh để lộ chi tiết ràng buộc "
            "trong lỗi, và coi RLS là cơ chế hiển thị dòng cho truy vấn chứ không "
            "phải để ẩn sự tồn tại của khóa."
        ),
        tags=["postgresql", "security", "rls"],
    ),
    # HARD: 1 essay (difficulty 4)
    essay_vi(
        "secb-hard-compromised-app-role",
        ["PG-PRIVILEGE", "PG-RLS", "PG-ROLES"],
        4,
        (
            "An attacker obtains the credentials of the application's database "
            "role. Threat-model the damage and design defense in depth. Cover role "
            "privileges, RLS, schema ownership, SECURITY DEFINER code, network and "
            "authentication controls, auditing and response."
        ),
        (
            "With the application role's credentials, the attacker can do whatever "
            "that role can do, from whatever network location the authentication "
            "rules allow. Least privilege limits the blast radius: the role should "
            "have only required DML on required tables, no superuser, BYPASSRLS, "
            "CREATEDB, CREATEROLE or DDL, should not own tables, and should not be "
            "able to read unrelated schemas. RLS should be enabled with FORCE where "
            "appropriate, and the role must not bypass it; SECURITY DEFINER "
            "functions must be minimal, owned by a dedicated role, and set a safe "
            "search_path, because a compromised caller may reach them. Network "
            "controls should restrict where the role can connect, require TLS, and "
            "use strong SCRAM authentication or certificates; secrets should be "
            "rotated and never embedded in client code. Auditing should record "
            "connections and privileged operations, monitor unusual query volume, "
            "and alert on errors. Response includes revoking or rotating the "
            "credential, terminating sessions, reviewing what was accessed, "
            "restoring from a known-good backup if integrity was affected, and "
            "closing the exposure that leaked the secret."
        ),
        (
            "The answer must connect the stolen role's exact privileges to the "
            "damage, then layer least privilege, RLS, definer safety, network and "
            "auth controls, audit and incident response."
        ),
        [
            "Assumes the database is safe because it is behind a firewall, or lists controls without linking them to the compromised role.",
            "Lists least privilege and RLS but omits network, authentication, audit or response.",
            "Covers privileges, RLS and several controls, but leaves a significant layer or response step vague.",
            "Links the role's privileges to damage, then covers least privilege, FORCE RLS, definer hardening, TLS and restricted network, audit and a concrete rotation and response plan.",
        ],
        [PG_PRIV, PG_RLS, PG_ROLES, PG_CONFIG, PG_CLIENT_AUTH_CH, PG_SASL],
        vi_prompt=(
            "Kẻ tấn công lấy được thông tin đăng nhập của role cơ sở dữ liệu mà ứng "
            "dụng dùng. Hãy mô hình hóa thiệt hại và thiết kế phòng thủ nhiều lớp. "
            "Bao gồm quyền của role, RLS, quyền sở hữu schema, mã SECURITY DEFINER, "
            "kiểm soát mạng và xác thực, kiểm toán và ứng phó."
        ),
        vi_reference=(
            "Với thông tin đăng nhập của role ứng dụng, kẻ tấn công làm được mọi "
            "điều role đó làm được, từ mọi vị trí mạng mà quy tắc xác thực cho phép. "
            "Đặc quyền tối thiểu giới hạn phạm vi: role chỉ nên có DML cần thiết "
            "trên bảng cần thiết, không superuser, BYPASSRLS, CREATEDB, CREATEROLE "
            "hay DDL, không sở hữu bảng và không đọc được schema không liên quan. "
            "Nên bật RLS với FORCE khi phù hợp và role không được bỏ qua; hàm "
            "SECURITY DEFINER phải tối giản, do role chuyên dụng sở hữu và đặt "
            "search_path an toàn, vì người gọi bị xâm nhập có thể chạm tới chúng. "
            "Kiểm soát mạng nên giới hạn nơi role kết nối, yêu cầu TLS và dùng xác "
            "thực SCRAM mạnh hoặc chứng chỉ; bí mật phải được xoay vòng và không "
            "nhúng trong mã máy khách. Kiểm toán nên ghi kết nối và thao tác đặc "
            "quyền, giám sát khối lượng truy vấn bất thường và cảnh báo lỗi. Ứng "
            "phó gồm thu hồi hoặc xoay vòng thông tin đăng nhập, kết thúc phiên, rà "
            "soát dữ liệu bị truy cập, phục hồi từ bản sao tốt nếu toàn vẹn bị ảnh "
            "hưởng và bịt lỗ hổng làm lộ bí mật."
        ),
        vi_explanation=(
            "Câu trả lời phải nối quyền chính xác của role bị đánh cắp với thiệt "
            "hại, rồi xếp lớp đặc quyền tối thiểu, RLS, an toàn definer, kiểm soát "
            "mạng và xác thực, kiểm toán và ứng phó sự cố."
        ),
        vi_criteria=[
            "Cho rằng cơ sở dữ liệu an toàn vì nằm sau tường lửa, hoặc liệt kê kiểm soát mà không gắn với role bị xâm nhập.",
            "Nêu đặc quyền tối thiểu và RLS nhưng bỏ sót mạng, xác thực, kiểm toán hoặc ứng phó.",
            "Bao quát quyền, RLS và nhiều kiểm soát, nhưng bỏ sót một lớp quan trọng hoặc bước ứng phó còn mơ hồ.",
            "Nối quyền của role với thiệt hại, rồi bao quát đặc quyền tối thiểu, FORCE RLS, siết definer, TLS và mạng hạn chế, kiểm toán cùng kế hoạch xoay vòng và ứng phó cụ thể.",
        ],
        tags=["postgresql", "security", "threat-model"],
    ),
]
