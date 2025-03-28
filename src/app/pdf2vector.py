import os
import weaviate
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Weaviate
from weaviate.classes.config import Configure


# "/Users/jerry/Documents/book/english/child_engilsh.pdf"
def weaviate_init(file_path, index_name="child_english"):
    http_host = "localhost"
    grpc_host = "localhost"
    client = weaviate.connect_to_custom(
        http_host=http_host,  # Hostname for the HTTP API connection
        http_port=8080,  # Default is 80, WCD uses 443
        http_secure=False,  # Whether to use https (secure) for the HTTP API connection
        grpc_host=grpc_host,  # Hostname for the gRPC API connection
        grpc_port=50051,  # Default is 50051, WCD uses 443
        grpc_secure=False,  # Whether to use a secure channel for the gRPC API connection
        auth_credentials=None,  # API key for authentication
    )
    print(client.is_ready())
    all_indexs = client.collections.list_all()
    if any(index_name.lower() == k.lower() for k in all_indexs.keys()):
        print(f"✅ Collection `{index_name}` 已存在，无需创建。")
    else:
        client.collections.create(
            name=index_name,
            vectorizer_config=[
                Configure.NamedVectors.text2vec_ollama(
                    name="title_vector",
                    source_properties=["title"],
                    api_endpoint="http://host.docker.internal:11434",
                    model="snowflake-arctic-embed:335m",
                )
            ],
        )
    print(f"✅ Collection `{index_name}` 创建成功！")
    source_objects = [
        {
            "title": "The Shawshank Redemption",
            "description": "A wrongfully imprisoned man forms an inspiring friendship while finding hope and redemption in the darkest of places.",
        },
        {
            "title": "The Godfather",
            "description": "A powerful mafia family struggles to balance loyalty, power, and betrayal in this iconic crime saga.",
        },
        {
            "title": "The Dark Knight",
            "description": "Batman faces his greatest challenge as he battles the chaos unleashed by the Joker in Gotham City.",
        },
        {
            "title": "Jingle All the Way",
            "description": "A desperate father goes to hilarious lengths to secure the season's hottest toy for his son on Christmas Eve.",
        },
        {
            "title": "A Christmas Carol",
            "description": "A miserly old man is transformed after being visited by three ghosts on Christmas Eve in this timeless tale of redemption.",
        },
    ]

    collection = client.collections.get(index_name)
    with collection.batch.dynamic() as batch:
        for src_obj in source_objects:
            # The model provider integration will automatically vectorize the object
            batch.add_object(
                properties={
                    "title": src_obj["title"],
                    "description": src_obj["description"],
                },
                # vector=vector  # Optionally provide a pre-obtained vector
            )
            if batch.number_errors > 10:
                print("Batch import stopped due to excessive errors.")
                break

    failed_objects = collection.batch.failed_objects
    if failed_objects:
        print(f"Number of failed imports: {len(failed_objects)}")
        print(f"First failed object: {failed_objects[0]}")

    collection = client.collections.get(index_name)
    response = collection.query.near_text(
        query="Shawshank Carol",  # The model provider integration will automatically vectorize the query
        limit=2,
    )

    for obj in response.objects:
        print(obj.properties["title"])
