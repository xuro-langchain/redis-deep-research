# Connecting Deep Research Agent to Amazon OpenSearch MCP Service

This guide explains how to connect your deep research agent to Amazon OpenSearch Service via the Model Context Protocol (MCP).

## Important: Authentication Architecture

**Why Supabase?** The current implementation uses Supabase tokens, but this doesn't mean Supabase is authenticating directly with AWS OpenSearch. Here's how it works:

1. **Your application** authenticates users (e.g., via Supabase, AWS Cognito, or another identity provider)
2. **OpenSearch MCP Server** (deployed on AWS) has an OAuth endpoint that accepts tokens from your identity provider
3. **Token Exchange**: The MCP server exchanges your identity token for an MCP access token
4. **AWS OpenSearch**: The MCP server uses AWS IAM roles internally to access OpenSearch (transparent to your agent)

So Supabase (or your identity provider) → authenticates users → MCP server → uses AWS IAM → accesses OpenSearch.

See [Step 3: Authentication Setup](#step-3-authentication-setup) for detailed explanations and alternatives.

## Prerequisites

1. An Amazon OpenSearch Service domain (or you'll need to create one)
2. AWS account with appropriate permissions
3. Access to AWS Console or AWS CLI/CloudFormation

## Step 1: Deploy the OpenSearch MCP Server

Amazon provides an MCP server integration template that you can deploy via Amazon Bedrock AgentCore:

### Option A: Using AWS Console (Recommended)

1. **Navigate to OpenSearch Service Console**
   - Go to AWS Console → Amazon OpenSearch Service
   - Select your OpenSearch domain (or create a new one)

2. **Access Integrations**
   - In the left navigation pane, select **Integrations**
   - Locate the **MCP server integration template**
   - Click **Configure domain**

3. **Configure the MCP Server**
   - Enter your OpenSearch domain endpoint
   - The template will create:
     - Amazon ECR repository for the MCP server
     - Amazon Cognito user pool for OAuth authentication
     - Execution role for AgentCore Runtime
     - MCP server endpoint URL

4. **Set Up Permissions**
   - Map your execution role ARN to an OpenSearch backend role
   - This controls access to your OpenSearch domain

5. **Obtain Access Information**
   - Get the OAuth access token from your authorizer
   - Note the MCP server URL from CloudFormation stack outputs

### Option B: Using CloudFormation

You can also deploy the MCP server using AWS CloudFormation. Refer to the [AWS documentation](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/cfn-template-mcp-server.html) for the CloudFormation template.

## Step 2: Configure Your Agent

Once the MCP server is deployed, configure your agent to connect to it. The agent already has built-in MCP support - you just need to provide the configuration.

### Configuration Options

There are three ways to configure the MCP connection:

#### Option 1: Via LangGraph Studio UI

1. Launch LangGraph Studio:
   ```bash
   uvx --refresh --from "langgraph-cli[inmem]" --with-editable . --python 3.11 langgraph dev --allow-blocking
   ```

2. In the Studio UI:
   - Go to **Manage Assistants** tab
   - Find the **mcp_config** field
   - Configure:
     - **url**: Your MCP server URL (from CloudFormation stack outputs)
     - **tools**: List of OpenSearch tool names you want to enable (e.g., `["search", "query"]`)
     - **auth_required**: Set to `true` (OpenSearch MCP requires authentication)

3. In the **mcp_prompt** field (optional):
   - Add instructions about OpenSearch tools availability
   - Example: "You have access to Amazon OpenSearch tools for searching and querying indexed documents."

#### Option 2: Via Environment Variables

Set these environment variables before running your agent:

```bash
export MCP_CONFIG_URL="https://your-mcp-server-url.amazonaws.com"
export MCP_CONFIG_TOOLS='["search", "query"]'  # JSON array of tool names
export MCP_CONFIG_AUTH_REQUIRED="true"
export MCP_PROMPT="You have access to Amazon OpenSearch tools for searching indexed documents."
```

#### Option 3: Via Runtime Configuration

When invoking the agent programmatically, pass the configuration:

```python
from agent.configuration import Configuration, MCPConfig

config = {
    "configurable": {
        "mcp_config": {
            "url": "https://your-mcp-server-url.amazonaws.com",
            "tools": ["search", "query"],  # Tool names from your MCP server
            "auth_required": True
        },
        "mcp_prompt": "You have access to Amazon OpenSearch tools for searching indexed documents.",
        "x-supabase-access-token": "your-oauth-token"  # Required if auth_required=True
    }
}

# Use config when invoking the agent
response = await graph.ainvoke({"messages": [{"role": "user", "content": "Your query"}]}, config)
```

## Step 3: Authentication Setup

### Understanding the Authentication Architecture

**Important**: The authentication flow uses **OAuth token exchange**, not direct AWS authentication:

1. **User Identity Provider** (e.g., Supabase) → Issues identity token
2. **OpenSearch MCP Server** (deployed on AWS) → Has OAuth endpoint that accepts identity tokens
3. **Token Exchange** → MCP server exchanges identity token for MCP access token
4. **Agent** → Uses MCP access token to authenticate with OpenSearch MCP server

The OpenSearch MCP server (deployed via AWS Bedrock AgentCore) is configured during deployment to trust tokens from your identity provider (typically Supabase or AWS Cognito). The MCP server handles the actual AWS OpenSearch authentication internally using IAM roles.

### Authentication Flow Diagram

```
┌─────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   User      │         │  OpenSearch MCP  │         │  AWS OpenSearch │
│             │         │     Server       │         │     Service     │
│             │         │   (on AWS)       │         │                 │
└──────┬──────┘         └────────┬─────────┘         └────────┬────────┘
       │                        │                            │
       │ 1. Supabase Token      │                            │
       ├───────────────────────>│                            │
       │                        │                            │
       │ 2. Exchange Token      │                            │
       │    POST /oauth/token   │                            │
       ├───────────────────────>│                            │
       │                        │                            │
       │ 3. MCP Access Token    │                            │
       │<───────────────────────┤                            │
       │                        │                            │
       │ 4. API Calls with      │                            │
       │    Bearer Token        │                            │
       ├───────────────────────>│                            │
       │                        │                            │
       │                        │ 5. IAM Role Authentication │
       │                        ├───────────────────────────>│
       │                        │                            │
       │                        │ 6. OpenSearch API Calls    │
       │                        ├───────────────────────────>│
       │                        │                            │
       │                        │ 7. Results                │
       │                        │<───────────────────────────┤
       │                        │                            │
       │ 8. Search Results      │                            │
       │<───────────────────────┤                            │
       │                        │                            │
```

### Using Supabase Token Exchange (Current Implementation)

The current code implementation expects Supabase tokens and exchanges them for MCP tokens:

1. **Obtain Supabase Token**
   - Get a valid Supabase access token from your authentication system
   - This token identifies the user in your application

2. **Configure Token in Runtime Config**
   ```python
   config = {
       "configurable": {
           "x-supabase-access-token": "your-supabase-token",
           "mcp_config": {
               "url": "https://your-mcp-server-url.amazonaws.com",
               "tools": ["search", "query"],
               "auth_required": True
           }
       },
       "metadata": {
           "owner": "user-id-123"  # Required for token caching
       }
   }
   ```

3. **Token Exchange Flow**
   - The agent calls `{mcp_server_url}/oauth/token` with your Supabase token
   - The MCP server validates the token and returns an MCP access token
   - The MCP access token is cached and used for subsequent requests
   - Tokens are automatically refreshed when expired

### Alternative: Using AWS Cognito Directly

If your OpenSearch MCP server is configured to use AWS Cognito instead of Supabase:

**Option 1: Modify the Token Exchange Function**

You can modify `fetch_tokens()` in `src/agent/utils.py` to accept Cognito tokens directly:

```python
async def fetch_tokens(config: RunnableConfig) -> dict[str, Any]:
    """Fetch and refresh MCP tokens, obtaining new ones if needed."""
    # Try to get existing valid tokens first
    current_tokens = await get_tokens(config)
    if current_tokens:
        return current_tokens
    
    # Option 1: Try Cognito token first (if configured)
    cognito_token = config.get("configurable", {}).get("x-cognito-access-token")
    if cognito_token:
        mcp_config = config.get("configurable", {}).get("mcp_config")
        if mcp_config and mcp_config.get("url"):
            mcp_tokens = await get_mcp_access_token(cognito_token, mcp_config.get("url"))
            if mcp_tokens:
                await set_tokens(config, mcp_tokens)
                return mcp_tokens
    
    # Option 2: Fall back to Supabase token exchange (existing logic)
    supabase_token = config.get("configurable", {}).get("x-supabase-access-token")
    # ... rest of existing code
```

**Option 2: Use Direct MCP Access Token**

If you already have an MCP access token (obtained outside the agent), you can bypass token exchange by modifying `load_mcp_tools()`:

```python
# In load_mcp_tools(), replace token fetching with direct token:
mcp_access_token = config.get("configurable", {}).get("mcp_access_token")
if mcp_access_token:
    auth_headers = {"Authorization": f"Bearer {mcp_access_token}"}
```

### Using AWS IAM Credentials (Advanced)

For direct AWS authentication without MCP server's OAuth endpoint, you would need to:

1. **Modify the MCP Client Configuration** to use AWS SigV4 signing
2. **Update `load_mcp_tools()`** to use AWS credentials instead of Bearer tokens

This requires more substantial code changes and is typically not needed since the MCP server handles AWS authentication internally via IAM roles.

## Step 4: Verify Connection

After configuration, verify the connection:

1. **Check Tool Loading**
   - The agent logs will show MCP tools being loaded
   - Check for any authentication errors

2. **Test a Query**
   - Ask a research question that would benefit from OpenSearch
   - The agent should automatically use OpenSearch tools when relevant

3. **Monitor Logs**
   - Watch for MCP connection errors
   - Check authentication token refresh messages

## Available OpenSearch Tools

The specific tools available depend on your MCP server configuration. Common OpenSearch MCP tools include:

- **search**: Search indexed documents
- **query**: Execute complex queries
- **index**: Index new documents (if configured)
- **retrieve**: Retrieve specific documents by ID

Check your MCP server documentation or CloudFormation outputs for the exact tool names.

## Troubleshooting

### Authentication Errors

- **Error: "Required interaction"**: Your OAuth token may be expired or invalid
- **Solution**: Refresh your Supabase token or check token exchange endpoint

### Connection Errors

- **Error: "Failed to connect to MCP server"**: 
  - Verify the MCP server URL is correct
  - Check that the server is running and accessible
  - Verify network connectivity

### Tool Not Found Errors

- **Error: "Tool 'search' not found"**:
  - Verify tool names match exactly what your MCP server provides
  - Check the `tools` list in your configuration

### Token Expiration

- Tokens are automatically refreshed when expired
- If refresh fails, you may need to re-authenticate with Supabase

## Example Configuration

Here's a complete example configuration:

```python
from agent.configuration import Configuration

# Create configuration
config = {
    "configurable": {
        # MCP Configuration
        "mcp_config": {
            "url": "https://opensearch-mcp-123456789.us-east-1.amazonaws.com",
            "tools": ["search", "query", "retrieve"],
            "auth_required": True
        },
        "mcp_prompt": (
            "You have access to Amazon OpenSearch tools for searching and querying "
            "indexed documents. Use these tools when you need to search internal "
            "knowledge bases or document repositories."
        ),
        
        # Authentication (required if auth_required=True)
        "x-supabase-access-token": "your-supabase-access-token-here",
        
        # Other agent settings
        "research_model": "openai:gpt-4.1",
        "search_api": "tavily",
        # ... other configuration options
    },
    "metadata": {
        "owner": "user-id-123"  # Required for token storage
    }
}
```

## Additional Resources

- [AWS OpenSearch MCP Server Documentation](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/cfn-template-mcp-server.html)
- [Hosting OpenSearch MCP Server with Amazon Bedrock AgentCore](https://opensearch.org/blog/hosting-opensearch-mcp-server-with-amazon-bedrock-agentcore/)
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)

## Code Reference

The MCP integration code is located in:
- `src/agent/utils.py` - `load_mcp_tools()`, `fetch_tokens()`, `get_mcp_access_token()`
- `src/agent/configuration.py` - `MCPConfig` class
- `src/agent/graph.py` - Uses `get_all_tools()` which includes MCP tools

