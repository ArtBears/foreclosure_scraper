import sqlite3

# Step 1: Connect to SQLite database (it will create the database file if it doesn't exist)
conn = sqlite3.connect('documents.db')

# Step 2: Create a table for storing document IDs
conn.execute('''
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    document_id TEXT UNIQUE NOT NULL,
    document_link TEXT UNIQUE NOT NULL
)
''')
conn.commit()

def insert_document_id(doc_id, doc_link) -> bool:
    """
    Inserts a new document ID into the database.
    """
    try:
        conn.execute('INSERT INTO documents (document_id, document_link) VALUES (?, ?)', (doc_id, doc_link))
        conn.commit()
        return True
    except sqlite3.IntegrityError: # This will occur if the document_id is already in the database
        return False

def check_document_id_exists(doc_id) -> bool:
    """
    Checks if the given document ID already exists in the database.
    """
    cursor = conn.execute('SELECT 1 FROM documents WHERE document_id = ?', (doc_id,))
    return cursor.fetchone() is not None
