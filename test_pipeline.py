import asyncio
from server.pipeline.session import session_manager
from server.app import _process_query, load_knowledge

async def main():
    print("Loading knowledge...")
    await load_knowledge()
    
    session = session_manager.get_or_create("test-session")
    session.language = "en"
    
    query = "What are the B.Tech courses available?"
    print(f"\nUser: {query}")
    
    result = await _process_query(query, session)
    print(f"\nVelBot: {result['text']}")
    print(f"Meta: Intent={result['intent']}, Strategy={result['strategy']}, Domains={result['domains']}")

if __name__ == "__main__":
    asyncio.run(main())
