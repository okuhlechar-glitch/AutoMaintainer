---
name: llm-structured-output-robustness
description: Handle LLM responses that fail JSON parsing when using free-tier OpenAI-compatible proxies (OpenRouter, etc.) — extract JSON from markdown fences, prose wrappers, and add retry logic.
source: auto-skill
extracted_at: '2026-06-17T10:45:54.862Z'
---

# Robust LLM Structured Output via OpenAI-Compatible Proxies

Use this when an app calls an LLM through an OpenAI-compatible proxy (OpenRouter, Groq, Azure, etc.) and expects JSON output, but the model doesn't reliably honor `response_format={"type": "json_object"}`. Free-tier and smaller models (7-8B params) frequently:
- Wrap JSON in markdown code fences (`\`\`\`json ... \`\`\``)
- Add explanatory prose before or after the JSON block
- Return partial or malformed JSON

This causes `json.loads()` to fail silently, and downstream agents receive empty data — pipelines "succeed" with zero output.

## Step 1: Add multi-strategy JSON extraction

Replace naive `json.loads(output)` with a method that tries multiple extraction strategies:

```python
def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
    # 1. Direct parse (works when model actually honors response_format)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Strip markdown fences (```json ... ``` or ``` ... ```)
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 3. First balanced brace block (handles prose before JSON)
    brace_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    # 4. Greedy brace match (deeply nested JSON with many levels)
    greedy_match = re.search(r"\{.*\}", text, re.DOTALL)
    if greedy_match:
        try:
            return json.loads(greedy_match.group(0))
        except json.JSONDecodeError:
            pass

    return None
```

## Step 2: Add retry with correction prompts

When extraction fails, don't silently return `{"raw_response": output}` — retry with explicit correction:

```python
for attempt in range(retries + 1):
    output = await self.chat(messages=messages, response_format={"type": "json_object"})
    parsed = self._extract_json(output)
    if parsed is not None:
        return parsed

    # Append failed response + correction instruction to the conversation
    messages.append({"role": "assistant", "content": output})
    messages.append({
        "role": "user",
        "content": "Your previous response was not valid JSON. Return ONLY a JSON object with no markdown fences, no commentary, no extra text.",
    })
```

## Step 3: Surface failure clearly, don't hide it

If all retries fail, return an explicit error signal instead of an empty dict:

```python
return {"raw_response": output, "error": "failed_to_parse_json"}
```

Downstream agents should check for `error` key and react accordingly (retry, abort, or log).

## Step 4: Add retry logic at the agent level too

The consuming agent (e.g., DeveloperAgent) should retry when it receives empty results:

```python
for attempt in range(1, max_retries + 1):
    result = await self.analyze(dev_prompt)
    if result.get("error") == "failed_to_parse_json":
        continue
    code_changes = [CodeChange(...) for c in result.get("changes", [])]
    if code_changes:
        break
```

## Step 5: Upgrade to models that support `response_format`

Root-cause fix: use models that actually support `response_format: json_object`. On OpenRouter, check the `/api/v1/models` endpoint for `structured_outputs` or `response_format` support flags. As of June 2026, free models that support it include:
- `openrouter/owl-alpha` (structured_outputs + response_format)
- `nex-agi/nex-n2-pro:free` (structured_outputs + response_format)
- `google/gemma-4-31b-it:free` (response_format only)

Avoid 7-8B models (llama-3.1-8b, qwen-2-7b, deepseek-r1-7b) for structured output — they lack `response_format` support and frequently wrap JSON in markdown.

## Step 6: Validate pipeline outputs before merge/push

When a pipeline produces code changes that will be committed/pushed:
- Check `code_changes` is non-empty before attempting PR creation
- On PR creation failure, set pipeline status to `FAILED` (not `APPROVED` with a garbled pr_url)
- Surface the error message clearly so the user can diagnose

## Step 7: Handle merge/push failures explicitly

When empty code changes flow through to the approval/merge stage, the pipeline can silently "succeed" with nothing to push. Fix the merge handler:

```python
async def approve_pipeline(self, pipeline_id: str):
    # Validate code changes exist before attempting PR
    if not pipeline.code_changes:
        raise ValueError("Pipeline has no code changes to push")

    try:
        # ... create branch, commit, PR ...
        pipeline.status = PipelineStatus.MERGED
    except Exception as e:
        # Set FAILED status, not APPROVED with garbled pr_url
        pipeline.status = PipelineStatus.FAILED
        pipeline.error_message = f"PR creation failed: {e}"
```

The old code set `pr_url = f"PR creation failed: {e}"` and left status as `APPROVED` — this meant the dashboard showed a "successful" pipeline with a broken URL string, confusing users.

## Step 8: Don't pass `max_tokens` — let the model use its natural output limit

When calling LLM APIs for structured output that contains **full file contents** (CSS, HTML, code files), passing a fixed `max_tokens` cap (e.g., 4096) silently truncates the response mid-JSON. The truncated JSON looks valid at the start (`{ "changes": [...]`) but is missing closing braces, making it unparseable even by the extraction strategies above.

The error manifests as: `LLM returned non-JSON response: { "changes": [ { "file_path": "...", "new_content": "/* ...` — the JSON starts correctly but gets cut off.

**Fix:** Don't include `max_tokens` in the API kwargs at all (unless explicitly needed for a specific use case). Let the model use its natural maximum output length:

```python
# Before (truncates long responses):
kwargs = {
    "model": self.model,
    "messages": messages,
    "max_tokens": max_tokens or self.config.max_tokens,  # caps at 4096
}

# After (no artificial cap — model outputs up to its natural limit):
kwargs = {
    "model": self.model,
    "messages": messages,
}
if max_tokens is not None:
    kwargs["max_tokens"] = max_tokens  # only when explicitly requested
```

The OpenAI-compatible API will default to the model's maximum output capacity when `max_tokens` is omitted. For free-tier OpenRouter models, this is typically 4K–8K tokens — but **not passing it** ensures you get the maximum the model can produce, rather than artificially capping below that.

Also remove `max_tokens` from `ModelConfig` defaults if it was set to a low value (e.g., 4096). The field can stay but should only be used when an explicit override is needed.

## Why this works

- **Multi-strategy extraction**: Handles the 3 most common free-model failure modes (fences, prose, partial JSON)
- **Retry with correction**: Models often succeed on the 2nd attempt when told "return only JSON"
- **Explicit failure signals**: Prevents silent "empty pipeline" successes that waste user time
- **Model selection**: Using models that honor `response_format` eliminates the problem at the root
- **Explicit merge failure handling**: Prevents dashboard showing "success" when PR creation actually failed
- **No artificial max_tokens cap**: Prevents truncation of long structured responses (full file contents) that would otherwise produce valid but cut-off JSON
