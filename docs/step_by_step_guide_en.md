# Step-by-Step Configuration Guide

**Please perform all operations on a computer.**

Why is there no Semantic Scholar API Key included? Because the author couldn't get one either... (*￣︿￣)

I'm sorry that some of the pictures are in Chinese. If you have any questions, please feel free to ask.

## 1. Apply for Scopus API Key

Go to the following website to apply for an API Key:

https://dev.elsevier.com/

![image-20260121000131000](images/image-20260121000131000_1.png)

Note: You need to register with an institutional email address and verify your affiliation with the corresponding educational institution. Do not disclose the obtained API Key, as it may be misused by others.

## 2. Download Cherry Studio

Go to this website to download the PC version of Cherry Studio: https://www.cherry-ai.com/

After opening it, you will find that a free GLM model is already configured by default.

Go to the MCP Servers tab in Settings:

<img src="images/image-20260121141003426_1.png" alt="image-20260121141003426" style="zoom: 50%;" />

<img src="images/image-20260121173914175.png" alt="image-20260121173914175" style="zoom: 80%;" />

On first launch, a warning sign will appear in the top right corner. **Please make sure to click it to install necessary dependencies.**

![image-20260121174054979](images/image-20260121174054979.png)

Click install and wait for the installation to complete.

![image-20260121174238635](images/image-20260121174238635.png)

**You must ensure the icon here turns into a "√".** If any dependency installation issues occur here, please go to the Cherry Studio project page to submit an issue.

## 3. Import JSON File

Click "Add" in the top right corner, select "Import from JSON", and enter the "spell" below. Note that you should replace the KEY obtained in step 1 into it:

<img src="images/image-20260121141148036_1.png" alt="image-20260121141148036" style="zoom: 67%;" />

```json
{
  "mcpServers": {
    "uniarticles-mcp-server": {
      "command": "uvx",
      "args": [
        "--refresh", // If you do not want to force a refresh, remove this line
        "uniarticles-mcp"
      ],
      "env": {
        "SCOPUS_API_KEY": "your_scopus_api_key_here",
      }
    }
  }
}
```

**Please pay attention to the indentation of this JSON code!! Any improper indentation may cause the server import to fail!!!**

**If you do not currently hold any API Key**, enter the following token instead:

```json
{
  "mcpServers": {
    "uniarticles-mcp-server": {
      "command": "uvx",
      "args": [
        "--refresh",
        "uniarticles-mcp"
      ],
      "env": {
      }
    }
  }
}
```

**If you have successfully applied for a Semantic Scholar API Key**, then enter the following json instead:

```json
{
  "mcpServers": {
    "uniarticles-mcp-server": {
      "command": "uvx",
      "args": [
        "--refresh",
        "uniarticles-mcp"
      ],
      "env": {
        "SCOPUS_API_KEY": "your_scopus_api_key_here",
        "SEMANTIC_SCHOLAR_API_KEY": "your_semantic_scholar_api_key_here"
      }
    }
  }
}
```

Then, click here to start the service:

![image-20260310105636416](images/image-20260310105636416.png)

You must ensure that a version number like "1.X" appears in the bottom left corner. If only the "STDIO" label is shown, it means the service was not started correctly. It is recommended to delete and re-import.

## 4. Start Chatting

Finally, return to the chat interface and enable the "Call MCP Servers during chat" function:

![image-20260121143607708](images/image-20260121143607708_1.png)

![image-20260310105759234](images/image-20260310105759234.png)

Then you can ask the AI to search for literature!

![image-20260310105850211](images/image-20260310105850211.png)

If the MCP server name appears here, it proves the tool was called normally. **If not, even if the AI claims to have found some literature in Scopus, it is likely fabricated by the AI and its authenticity cannot be guaranteed.**

If the AI doesn't realize it needs to call this tool, you can emphasize in the prompt: `Use MCP tools to search in major databases`.

Click the ">" button to see that the large model essentially sent a query request to the database—query is the request topic (including "molecular fingerprint"), count is the number of queries, and some other parameters.

![image-20260310110009802](images/image-20260310110009802.png)

Therefore, **the literature obtained by the AI comes directly from the database query and must be authentic.** It will completely solve the hallucination problem when AI searches for literature.
