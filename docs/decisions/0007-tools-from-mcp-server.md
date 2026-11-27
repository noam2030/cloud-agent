# 7. Tools come from a separate MCP server

**Context:** The model should be able to use tools (starting with the current time), and the tools should be reusable by other AI clients.

**Decision:** Tools live in a separate repo and service, [`cloud-mcp`](https://github.com/noam2030/cloud-mcp), an MCP server on a private Cloud Run service. `agent.py` loads its tools with `langchain-mcp-adapters` and runs a LangChain `create_agent` loop: the model may call tools, read the results, then answer.

**Why:**
- MCP is the standard way to give agents tools. The same server works with Claude Desktop, Cursor, or other agents.
- The tool service deploys and scales on its own.

**Security:** The MCP service is private. Only `cloud-agent-runtime` has `run.invoker` on it, and the backend sends a Google ID token (audience = the service URL) with each call.

**Alternatives:** Plain Python functions as LangChain tools in `agent.py`. That's simpler if only this app will ever use them.

**Tradeoffs:**
- One more service to run.
- An extra network round trip to list tools on each chat request.
- If the MCP server is down, chat still works, just without tools.
- `langchain-mcp-adapters` needs the 1.x MCP client, while the server uses the 2.x SDK. The protocol is compatible, and this is tested.
