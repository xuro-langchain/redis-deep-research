"""
Example configuration for connecting to Amazon OpenSearch MCP Service.

This file demonstrates how to configure the deep research agent to connect
to an Amazon OpenSearch MCP server.
"""

from agent.configuration import Configuration, MCPConfig

# Example 1: Basic Configuration (No Authentication)
basic_config = {
    "configurable": {
        "mcp_config": {
            "url": "https://your-opensearch-mcp-server.amazonaws.com",
            "tools": ["search", "query"],  # List of tool names from your MCP server
            "auth_required": False
        },
        "mcp_prompt": (
            "You have access to Amazon OpenSearch tools for searching and querying "
            "indexed documents. Use these tools when you need to search internal "
            "knowledge bases or document repositories."
        ),
        # Other agent settings
        "research_model": "openai:gpt-4.1",
        "search_api": "tavily",
    }
}

# Example 2: Configuration with Authentication (OAuth Token Exchange)
authenticated_config = {
    "configurable": {
        "mcp_config": {
            "url": "https://your-opensearch-mcp-server.amazonaws.com",
            "tools": ["search", "query", "retrieve"],  # List of tool names
            "auth_required": True
        },
        "mcp_prompt": (
            "You have access to Amazon OpenSearch tools for searching and querying "
            "indexed documents. Use these tools when you need to search internal "
            "knowledge bases or document repositories."
        ),
        # Required for OAuth token exchange
        "x-supabase-access-token": "your-supabase-access-token-here",
        # Other agent settings
        "research_model": "openai:gpt-4.1",
        "search_api": "tavily",
    },
    "metadata": {
        "owner": "user-id-123"  # Required for token storage/retrieval
    }
}

# Example 3: Using Configuration Class Directly
def create_opensearch_config(
    mcp_server_url: str,
    tools: list[str],
    auth_required: bool = False,
    supabase_token: str = None,
    user_id: str = None
) -> dict:
    """Create a configuration dictionary for OpenSearch MCP connection.
    
    Args:
        mcp_server_url: URL of your OpenSearch MCP server
        tools: List of tool names to enable from the MCP server
        auth_required: Whether authentication is required
        supabase_token: Supabase access token (required if auth_required=True)
        user_id: User ID for token storage (required if auth_required=True)
    
    Returns:
        Configuration dictionary ready to use with the agent
    """
    config = {
        "configurable": {
            "mcp_config": {
                "url": mcp_server_url,
                "tools": tools,
                "auth_required": auth_required
            },
            "mcp_prompt": (
                "You have access to Amazon OpenSearch tools for searching and querying "
                "indexed documents. Use these tools when you need to search internal "
                "knowledge bases or document repositories."
            ),
            "research_model": "openai:gpt-4.1",
            "search_api": "tavily",
        }
    }
    
    if auth_required:
        if not supabase_token:
            raise ValueError("supabase_token is required when auth_required=True")
        if not user_id:
            raise ValueError("user_id is required when auth_required=True")
        
        config["configurable"]["x-supabase-access-token"] = supabase_token
        config["metadata"] = {"owner": user_id}
    
    return config

# Example usage:
if __name__ == "__main__":
    # Replace these with your actual values
    MCP_SERVER_URL = "https://opensearch-mcp-123456789.us-east-1.amazonaws.com"
    OPENSEARCH_TOOLS = ["search", "query", "retrieve"]
    SUPABASE_TOKEN = "your-supabase-access-token"
    USER_ID = "user-123"
    
    # Create configuration
    config = create_opensearch_config(
        mcp_server_url=MCP_SERVER_URL,
        tools=OPENSEARCH_TOOLS,
        auth_required=True,
        supabase_token=SUPABASE_TOKEN,
        user_id=USER_ID
    )
    
    print("Configuration created:")
    print(f"  MCP Server URL: {config['configurable']['mcp_config']['url']}")
    print(f"  Tools: {config['configurable']['mcp_config']['tools']}")
    print(f"  Auth Required: {config['configurable']['mcp_config']['auth_required']}")
    
    # Use this config when invoking the agent:
    # from agent.graph import graph
    # response = await graph.ainvoke(
    #     {"messages": [{"role": "user", "content": "Search for documents about..."}]},
    #     config
    # )

