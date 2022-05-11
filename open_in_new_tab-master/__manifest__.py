{
    "name": "Open odoo record in new tab",
    "author": "Ngasturi",
    "version": "14.0.1.0.1",
    "category": "Web",
    "website": "https://ngasturi.id",
    "summary": "",
    "description": """
            
        """,
    "depends": [
        "web" 
    ],
    "qweb": [
        "static/src/xml/template.xml"
    ],
     'assets': { 
         'web.assets_backend': [ 
            "/open_in_new_tab/static/src/js/many2one.js",
            "/open_in_new_tab/static/src/js/many2many.js",
            "/open_in_new_tab/static/src/js/tree_view.js",
         ] 
     }, 
    "license": 'AGPL-3', 
    "installable": True
}
