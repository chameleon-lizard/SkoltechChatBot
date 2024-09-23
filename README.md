# Skoltech chatbot 

Agentic RAG bot, which I made because I was bored. To run:

1. Add .env file with the following info:

```
BOT_TOKEN=<bot token>
TOKEN=<token for llm api>
JUDGE_API_LINK=<api link for judge llm for evals>
API_LINK=http://vllm:8001/v1
CHATBOT_MODEL=Qwen/Qwen2-7B-Instruct

JUDGE_MODEL=openai/gpt-4o-mini
RERANKER_MODEL=BAAI/bge-reranker-v2-m3
EMBEDDER_MODEL=intfloat/multilingual-e5-large-instruct
```

2. Run docker compose up:

```
docker compose up
```
