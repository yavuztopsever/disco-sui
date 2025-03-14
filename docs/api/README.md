# DiscoSui API Documentation

## Base URL

- Development: `http://localhost:5000`
- Production: `https://api.discosui.com`

## Authentication

All API requests require an OpenAI API key to be included in the request headers:

```
Authorization: Bearer your_openai_api_key
```

## Endpoints

### Chat

`POST /chat`

Send a message to the AI agent for processing.

#### Request Body

```json
{
  "message": "string"
}
```

#### Response

```json
{
  "success": true,
  "response": {
    "action": "string",
    "result": "string",
    "metadata": {}
  }
}
```

#### Error Response

```json
{
  "success": false,
  "response": "string",
  "error": "string"
}
```

### Health Check

`GET /health`

Check the health status of the API.

#### Response

```json
{
  "status": "healthy"
}
```

## Rate Limiting

- 100 requests per minute per API key
- Rate limit headers are included in the response:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

## Error Codes

- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 429: Too Many Requests
- 500: Internal Server Error

## WebSocket API

### Connection

`ws://localhost:5000/ws`

Connect to the WebSocket API for real-time updates.

#### Events

- `message`: Receive AI agent responses
- `error`: Receive error notifications
- `status`: Receive status updates

## Examples

### Python

```python
import requests

headers = {
    'Authorization': 'Bearer your_openai_api_key',
    'Content-Type': 'application/json'
}

response = requests.post(
    'http://localhost:5000/chat',
    headers=headers,
    json={'message': 'Create a new note about AI'}
)

print(response.json())
```

### JavaScript

```javascript
const response = await fetch('http://localhost:5000/chat', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer your_openai_api_key',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: 'Create a new note about AI'
  })
});

const data = await response.json();
console.log(data);
``` 