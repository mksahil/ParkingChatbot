# milvus_utils.py
from pymilvus import connections, utility, Collection, CollectionSchema, FieldSchema, DataType
from sentence_transformers import SentenceTransformer # For embeddings
import os

MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
COLLECTION_NAME = "parking_conversations"
EMBEDDING_DIM = 384 # Based on 'all-MiniLM-L6-v2'
INDEX_FIELD_NAME = "embedding"
ID_FIELD_NAME = "id"
TEXT_FIELD_NAME = "text"
METADATA_FIELD_NAME = "metadata" # Store user_id, timestamp, role, extracted_entities

# Initialize embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def get_milvus_connection():
    try:
        connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
        print(f"Connected to Milvus at {MILVUS_HOST}:{MILVUS_PORT}")
    except Exception as e:
        print(f"Failed to connect to Milvus: {e}")
        raise

def create_milvus_collection_if_not_exists():
    get_milvus_connection()
    if not utility.has_collection(COLLECTION_NAME):
        fields = [
            FieldSchema(name=ID_FIELD_NAME, dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name=TEXT_FIELD_NAME, dtype=DataType.VARCHAR, max_length=65535), # Increased max_length
            FieldSchema(name=METADATA_FIELD_NAME, dtype=DataType.JSON), # For user_id, role, entities
            FieldSchema(name=INDEX_FIELD_NAME, dtype=DataType.FLOAT_VECTOR, dim=EMBEDDING_DIM)
        ]
        schema = CollectionSchema(fields, description="Parking conversation history")
        collection = Collection(COLLECTION_NAME, schema=schema)
        print(f"Collection '{COLLECTION_NAME}' created.")

        # Create an index
        index_params = {
            "metric_type": "L2", # Euclidean distance
            "index_type": "IVF_FLAT", # A common index type
            "params": {"nlist": 128} # Number of clusters
        }
        collection.create_index(field_name=INDEX_FIELD_NAME, index_params=index_params)
        print(f"Index created for field '{INDEX_FIELD_NAME}'.")
        collection.load() # Load collection into memory for searching
        print(f"Collection '{COLLECTION_NAME}' loaded.")
    else:
        collection = Collection(COLLECTION_NAME)
        collection.load()
        print(f"Collection '{COLLECTION_NAME}' already exists and is loaded.")
    return collection

def store_conversation_turn(text: str, metadata: dict):
    collection = create_milvus_collection_if_not_exists()
    embedding = embedding_model.encode(text).tolist()
    data = [
        [text],
        [metadata], # e.g., {"user_id": "user123", "role": "user", "timestamp": "...", "entities": {...}}
        [embedding]
    ]
    try:
        mr = collection.insert(data)
        # print(f"Inserted conversation turn, IDs: {mr.primary_keys}")
        return mr.primary_keys
    except Exception as e:
        print(f"Error inserting into Milvus: {e}")
        return None


def retrieve_relevant_history(query_text: str, user_id: str, top_k: int = 5):
    collection = create_milvus_collection_if_not_exists()
    query_embedding = embedding_model.encode(query_text).tolist()

    search_params = {
        "metric_type": "L2",
        "params": {"nprobe": 10}, # How many clusters to search
    }
    # Filter by user_id
    # Ensure metadata field is properly structured e.g. {"user_id": "some_user_id", ...}
    expr_filter = f"metadata['user_id'] == '{user_id}'"

    results = collection.search(
        data=[query_embedding],
        anns_field=INDEX_FIELD_NAME,
        param=search_params,
        limit=top_k,
        expr=expr_filter, # This is key for user-specific memory
        output_fields=[TEXT_FIELD_NAME, METADATA_FIELD_NAME] # Retrieve text and metadata
    )

    history = []
    for hits in results:
        for hit in hits:
            history.append({
                "text": hit.entity.get(TEXT_FIELD_NAME),
                "metadata": hit.entity.get(METADATA_FIELD_NAME),
                "distance": hit.distance
            })
    return sorted(history, key=lambda x: x['metadata'].get('timestamp', 0)) # Sort by timestamp if available