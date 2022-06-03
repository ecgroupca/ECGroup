Purpose: Contains customizations needed for Firefly's Approvals app workflow.

Structure:
```bash
├── COPYRIGHT                             - Novobi copyright file
├── LICENSE                               - Odoo copyright file/statements
├── README.md                             - Explanatory file
├── __init__.py                           - Python's compiling file
├── __manifest__.py                       - Module's information file
├── models                                - Contains database's models and framework dependencies         
│   │
│   ├── __init__.py
│   ├── approval_category.py              - Creates new approval type and onchange handler for the new type
│   ├── approval_product_line.py          - Analytic Account and Analytic Tags on product line level
│   └── approval_request.py               - Adds new fields and rewrites actions for the new type
└── views                                 - Contains views' customizations
    │
    ├── approval_category_views.xml       - Display/change require settings on fields accordingly
    ├── approval_product_line_views.xml   - Display/change require settings on fields accordingly
    └── approval_request_views.xml        - Display/change require settings on fields accordingly
```