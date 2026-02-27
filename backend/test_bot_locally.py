from app import create_app
import json

app = create_app()
client = app.test_client()

def test_chatbot(query):
    print(f"\nTesting Chatbot with query: '{query}'")
    response = client.post('/api/chatbot/message', 
                           data=json.dumps({'message': query}),
                           content_type='application/json')
    print(f"Status: {response.status_code}")
    print(f"Response: {response.get_json()}")

if __name__ == '__main__':
    test_chatbot("How do I mark attendance?")
    test_chatbot("What is gravity?")
    test_chatbot("Who is Albert Einstein?")
    test_chatbot("tell me about space")
