import asyncio
import json
import logging
import multiprocessing
import re
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from web_agent.agent.conversation_history import ConversationHistory
from web_agent.browser.session import BrowserSession
from web_agent.config.settings import Config
from web_agent.llm.llm_client import LLMClient
from web_agent.search.google_scraper import GoogleSearchScraper
from web_agent.skills.skill_manager import SkillManager
from web_agent.tools.file_analyzer import FileAnalyzer
from web_agent.tools.tool_definitions import execute_tool, get_all_tool_schemas

logger = logging.getLogger(__name__)

_URL_PATTERN = re.compile(
    r'(?:https?://)?(?:www\.)?([a-zA-Z0-9][-a-zA-Z0-9]*(?:\.[a-zA-Z0-9][-a-zA-Z0-9]*)+)',
    re.IGNORECASE,
)

_BUILTIN_DOMAINS = frozenset({
    "google.com", "bing.com", "yahoo.com", "duckduckgo.com", "baidu.com",
    "yandex.com", "wikipedia.org",
})


def extract_target_domains(request: str) -> list[str]:
    urls_or_domains = _URL_PATTERN.findall(request)
    return [d for d in urls_or_domains if d.lower() not in _BUILTIN_DOMAINS]


SYSTEM_PROMPT = """You are a web browsing agent. Your task is to browse the web and gather information to fulfill the user's request.

You have access to these tools:
1. browser - Control a web browser (navigate, click, type, extract text, etc.)
2. web_search - Search Google for information
3. web_fetch - Fetch and extract content from a URL

IMPORTANT RULES ABOUT SEARCHING:
- If the user specifies a specific website or domain (e.g., "search on amazon.com", "look at reddit.com"), DO NOT use web_search (Google). Instead, navigate directly to that website using the browser tool or use web_fetch on the specific URL.
- Only use web_search (Google) when the user wants a general web search with no specific site in mind.
- When a domain is specified, navigate directly to it, then use the site's own search or browse its pages.

Guidelines:
- Use web_fetch to extract content from specific pages
- Use the browser tool when you need to interact with a website
- Always extract and summarize the key information
- If you encounter a website you'velearned about before, check the skills for navigation instructions
- Report back with a clear, organized summary of your findings

{guardrails}

When browsing websites, follow any skill instructions that are provided to you."""


class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentResult:
    agent_id: str
    status: AgentStatus
    result: str = ""
    error: str = ""
    web_search_used: bool = False


class BrowsingAgent:
    def __init__(
        self,
        agent_id: str,
        task: str,
        config: Optional[Config] = None,
        skills_instructions: str = "",
        parent_result_queue: Optional[multiprocessing.Queue] = None,
        depth: int = 0,
        deep: bool = False,
        guardrails: str = "",
    ):
        self.agent_id = agent_id
        self.task = task
        self.config = config or Config()
        self.skills_instructions = skills_instructions
        self.parent_result_queue = parent_result_queue
        self.depth = depth
        self.deep = deep
        self.guardrails = guardrails
        self.llm = LLMClient(self.config)
        self.browser = BrowserSession(self.config)
        self.search_scraper = GoogleSearchScraper(self.config)
        self.skill_manager = SkillManager(self.config.effective_skills_dir)
        self.status = AgentStatus.PENDING
        self.messages: list[dict] = []
        self.max_iterations = self.config.max_agent_iterations
        self.web_search_used = False

    async def run(self) -> AgentResult:
        self.status = AgentStatus.RUNNING
        logger.info("Agent %s starting task: %s", self.agent_id, self.task[:100])

        try:
            await self.browser.start()
            self.skill_manager.load_skills()

            skill_context = ""
            relevant_skills = self.skill_manager.find_relevant_skills(self.task)
            if relevant_skills:
                skill_context = self.skill_manager.get_skill_instructions_for_prompt(self.task)

            system_prompt = SYSTEM_PROMPT.format(guardrails=self.guardrails)
            if self.skills_instructions:
                system_prompt += f"\n\n{self.skills_instructions}"
            if skill_context:
                system_prompt += f"\n\n## Relevant Skills\n\n{skill_context}"

            self.messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": self.task},
            ]

            for iteration in range(self.max_iterations):
                logger.debug("Agent %s iteration %d/%d", self.agent_id, iteration + 1, self.max_iterations)

                response = await self.llm.chat(
                    messages=self.messages,
                    tools=get_all_tool_schemas(),
                )

                assistant_message = response.get("message", {})
                self.messages.append(assistant_message)

                if response.get("done", False) and not _has_tool_calls(response):
                    final_content = assistant_message.get("content", "")
                    self.status = AgentStatus.COMPLETED
                    result = AgentResult(
                        agent_id=self.agent_id,
                        status=self.status,
                        result=final_content,
                        web_search_used=self.web_search_used,
                    )
                    if self.parent_result_queue:
                        self.parent_result_queue.put(result)
                    return result

                tool_calls = _extract_tool_calls(response)
                if tool_calls:
                    for tool_call in tool_calls:
                        if tool_call["name"] == "web_search":
                            self.web_search_used = True
                        tool_result = await execute_tool(
                            tool_name=tool_call["name"],
                            arguments=tool_call.get("arguments", {}),
                            browser=self.browser,
                            search_scraper=self.search_scraper,
                            config=self.config,
                            deep=self.deep,
                        )
                        self.messages.append({
                            "role": "tool",
                            "name": tool_call["name"],
                            "content": tool_result,
                        })
                else:
                    content = assistant_message.get("content", "")
                    if content:
                        self.status = AgentStatus.COMPLETED
                        result = AgentResult(
                            agent_id=self.agent_id,
                            status=self.status,
                            result=content,
                            web_search_used=self.web_search_used,
                        )
                        if self.parent_result_queue:
                            self.parent_result_queue.put(result)
                        return result

            self.status = AgentStatus.COMPLETED
            result = AgentResult(
                agent_id=self.agent_id,
                status=self.status,
                result="Agent reached maximum iterations without a final answer.",
                web_search_used=self.web_search_used,
            )
            if self.parent_result_queue:
                self.parent_result_queue.put(result)
            return result

        except Exception as e:
            logger.error("Agent %s failed: %s", self.agent_id, e)
            self.status = AgentStatus.FAILED
            result = AgentResult(
                agent_id=self.agent_id,
                status=self.status,
                error=str(e),
                web_search_used=self.web_search_used,
            )
            if self.parent_result_queue:
                self.parent_result_queue.put(result)
            return result
        finally:
            await self.browser.stop()


ANALYSIS_SYSTEM_PROMPT = """You are a document analysis agent. You receive file content and a user request to analyze, summarize, or review it.

{guardrails}

Guidelines:
- Provide thorough, well-organized analysis
- Highlight key points, patterns, and insights
- If summarizing, capture the essential information concisely
- If reviewing, note issues, strengths, and suggestions
- Use the language of the user's request for your response
- Format your response with clear sections and headers"""


class AnalysisAgent:
    def __init__(self, config: Optional[Config] = None, guardrails: str = ""):
        self.config = config or Config()
        self.guardrails = guardrails
        self.llm = LLMClient(self.config)
        self.file_analyzer = FileAnalyzer()

    async def analyze(self, request: str, file_paths: list[str]) -> str:
        logger.info("AnalysisAgent analyzing %d file(s): %s", len(file_paths), ", ".join(file_paths))

        files_data = self.file_analyzer.read_files(file_paths)

        file_sections = []
        errors = []
        for file_data in files_data:
            if "error" in file_data:
                errors.append(file_data["error"])
                continue
            file_name = file_data.get("name", "unknown")
            file_type = file_data.get("type", "unknown")
            content = file_data.get("content", "")
            if not content.strip():
                errors.append(f"The file '{file_name}' appears to be empty.")
                continue
            file_sections.append(f"### File: {file_name} (type: {file_type})\n\n{content}")

        if errors and not file_sections:
            return "Errors reading files:\n" + "\n".join(f"- {e}" for e in errors)

        combined_content = "\n\n---\n\n".join(file_sections)
        error_note = ""
        if errors:
            error_note = "\n\nNote: Some files could not be read:\n" + "\n".join(f"- {e}" for e in errors)

        prompt = f"""User request: {request}

Files provided ({len(file_sections)} file(s)):

{combined_content}
{error_note}

Please fulfill the user's request across all the provided files."""

        system = ANALYSIS_SYSTEM_PROMPT.format(guardrails=self.guardrails)
        response = await self.llm.chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )

        return response.get("message", {}).get("content", "").strip()


AI_FIRST_SYSTEM_PROMPT = """You are an intelligent assistant. Answer the user's question using your own knowledge first.

{guardrails}

IMPORTANT RULES:
- If you CAN answer the question with confidence using your existing knowledge, provide your answer directly.
- If you CANNOT answer confidently, or if the question requires CURRENT/UP-TO-DATE information (news, prices, recent events, real-time data), respond with EXACTLY: NEEDS_WEB_SEARCH
- If you have a partial answer but it may be outdated, respond with EXACTLY: NEEDS_WEB_SEARCH
- If the user specifies a particular website or domain to search on, respond with EXACTLY: NEEDS_WEB_SEARCH so the agent can browse that site directly (not via Google).
- Do NOT guess or make up information you are not sure about.
- Only respond with NEEDS_WEB_SEARCH if you genuinely cannot provide a reliable answer from your own knowledge.

Remember: for factual, historical, or general knowledge questions you know the answer to, just answer directly. Only use NEEDS_WEB_SEARCH when you truly need current or information you lack."""


ORCHESTRATOR_SYSTEM_PROMPT = """You are the main orchestrator agent. You receive requests from users and coordinate child agents to browse the web and gather information.

{guardrails}

You can:
1. Break down complex tasks into subtasks for child agents
2. Decide how many agents to spawn based on the task complexity
3. Combine results from multiple agents into a coherent response
4. Delegate web browsing tasks to specialized agents

Guidelines:
- For simple queries, handle directly
- For complex tasks, break them into focused subtasks for child agents
- Each child agent should have a clear, specific objective
- Combine and summarize the results before responding to the user
- If a task requires searching multiple topics, create one agent per topic and run them in parallel
- Maximum {max_subagents} subagents can run simultaneously
- Maximum nesting depth of {depth_limit} levels

Respond with a clear, organized summary of the information gathered."""


class OrchestratorAgent:
    def __init__(self, config: Optional[Config] = None, deep: bool = False):
        self.config = config or Config()
        self.deep = deep
        self.llm = LLMClient(self.config)
        self.skill_manager = SkillManager(self.config.effective_skills_dir)
        self.guardrails = self.config.load_guardrails()
        self.analysis_agent = AnalysisAgent(self.config, guardrails=self.guardrails)
        self.conversation_history = ConversationHistory(max_entries=self.config.max_history_entries)
        self.active_agents: dict[str, AgentResult] = {}

    async def handle_request(self, request: str, file_paths: Optional[list[str]] = None) -> str:
        logger.info("Orchestrator received request: %s", request[:200])

        if file_paths:
            logger.info("Mode: file analysis | Files: %s", ", ".join(file_paths))
            result = await self.analysis_agent.analyze(request, file_paths)
            self.conversation_history.add_entry(request, result, web_search_used=False)
            return result

        target_domains = extract_target_domains(request)
        history_context = self.conversation_history.get_context_for_prompt()

        if target_domains:
            logger.info("Step: domain-specific request detected → domains: %s (skipping Google search)", ", ".join(target_domains))
            self.skill_manager.load_skills()

            task = self._build_domain_task(request, target_domains)
            agent = BrowsingAgent(
                agent_id=str(uuid.uuid4()),
                task=task,
                config=self.config,
                depth=0,
                deep=self.deep,
                guardrails=self.guardrails,
            )
            result = await agent.run()
            web_used = result.web_search_used
            self.conversation_history.add_entry(request, result.result, web_search_used=web_used)
            if result.status == AgentStatus.COMPLETED:
                return result.result
            return f"Error: {result.error}"

        logger.info("Step: asking AI model for answer from knowledge...")

        ai_answer = await self._ask_ai_first(request, history_context)

        if ai_answer is not None:
            logger.info("Step: AI model answered from own knowledge (no web search)")
            self.conversation_history.add_entry(request, ai_answer, web_search_used=False)
            return ai_answer

        logger.info("Step: AI model needs updated/current info → browsing the web")

        self.skill_manager.load_skills()

        plan = await self._plan_task(request, history_context)

        if plan.get("direct", False):
            logger.info("Step: dispatching single browsing agent (direct search)")
            result = await self._handle_directly(request)
            web_used = isinstance(result, AgentResult) and result.web_search_used
            self.conversation_history.add_entry(request, result if isinstance(result, str) else result.result, web_search_used=web_used)
            if isinstance(result, AgentResult):
                if result.status == AgentStatus.COMPLETED:
                    return result.result
                return f"Error: {result.error}"
            return result
        else:
            subtasks = plan.get("subtasks", [{"task": request}])
            logger.info("Step: dispatching %d subagents for parallel web search", len(subtasks))
            return await self._dispatch_subagents(subtasks, request)

    def _build_domain_task(self, request: str, domains: list[str]) -> str:
        domain_list = ", ".join(domains)
        skill_context = ""
        relevant_skills = self.skill_manager.find_relevant_skills(request)
        if relevant_skills:
            skill_context = self.skill_manager.get_skill_instructions_for_prompt(request)

        task = f"""The user wants information from a specific website/domain: {domain_list}

Original request: {request}

INSTRUCTIONS:
- Do NOT use web_search (Google). Navigate DIRECTLY to the specified website/domain.
- Use the browser tool to go to {domains[0]} directly, then use the site's own search or browse its pages.
- If multiple domains are specified ({domain_list}), visit each one directly using web_fetch or browser navigate.
- Extract the relevant information from those sites."""

        if skill_context:
            task += f"""

Relevant skill instructions:
{skill_context}"""

        return task

    async def _ask_ai_first(self, request: str, history_context: str = "") -> Optional[str]:
        system = AI_FIRST_SYSTEM_PROMPT.format(guardrails=self.guardrails)
        if history_context:
            system += f"\n\n{history_context}"

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": request},
        ]

        response = await self.llm.chat(messages=messages)
        content = response.get("message", {}).get("content", "").strip()

        if "NEEDS_WEB_SEARCH" in content:
            logger.info("Step: AI model decided it cannot answer from knowledge → needs web search")
            return None

        if content:
            logger.info("Step: AI model provided answer from own knowledge")
            return content

        logger.info("Step: AI model returned empty response → falling back to web search")
        return None

    async def _plan_task(self, request: str, history_context: str = "") -> dict:
        system = "You are a task planner. Output only valid JSON."
        if self.guardrails:
            system += f"\n\n{self.guardrails}"
        if history_context:
            system += f"\n\n{history_context}"

        prompt = f"""Analyze this request and decide how to handle it:

Request: {request}

Respond in JSON format:
{{
    "direct": true/false,
    "subtasks": [
        {{"task": "specific subtask description"}}
    ]
}}

If the request is simple enough to handle with a single web search, set "direct" to true.
If it requires multiple independent investigations, break it into subtasks.
Maximum {self.config.max_subagents} subtasks."""

        response = await self.llm.chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )

        content = response.get("message", {}).get("content", "")

        try:
            cleaned = content.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            plan = json.loads(cleaned)
            return plan
        except json.JSONDecodeError:
            logger.warning("Failed to parse plan, defaulting to direct handling")
            return {"direct": True}

    async def _handle_directly(self, request: str) -> AgentResult:
        agent = BrowsingAgent(
            agent_id=str(uuid.uuid4()),
            task=request,
            config=self.config,
            depth=0,
            deep=self.deep,
            guardrails=self.guardrails,
        )
        return await agent.run()

    async def _dispatch_subagents(self, subtasks: list[dict], original_request: str) -> str:
        skill_context = self.skill_manager.get_skill_instructions_for_prompt(original_request)

        tasks = []
        for i, subtask in enumerate(subtasks[:self.config.max_subagents]):
            agent_id = f"subagent_{i}_{uuid.uuid4().hex[:8]}"
            task_desc = subtask.get("task", "")
            agent = BrowsingAgent(
                agent_id=agent_id,
                task=task_desc,
                config=self.config,
                skills_instructions=skill_context,
                depth=1,
                deep=self.deep,
                guardrails=self.guardrails,
            )
            tasks.append(agent.run())

        results = await asyncio.gather(*tasks, return_exceptions=True)

        subagent_results = []
        any_web_search = False
        for result in results:
            if isinstance(result, Exception):
                subagent_results.append(f"Agent failed: {str(result)}")
            elif result.status == AgentStatus.COMPLETED:
                subagent_results.append(result.result)
                if result.web_search_used:
                    any_web_search = True
            else:
                subagent_results.append(f"Agent error: {result.error}")

        combined = "\n\n---\n\n".join(
            f"**Subtask {i+1}:**\n{r}" for i, r in enumerate(subagent_results)
        )

        summary = await self._summarize_results(original_request, combined)
        self.conversation_history.add_entry(original_request, summary, web_search_used=any_web_search)
        return summary

    async def _summarize_results(self, original_request: str, combined_results: str) -> str:
        prompt = f"""Original request: {original_request}

Here are the results from multiple search agents:

{combined_results}

Please provide a comprehensive, well-organized summary that directly answers the original request."""

        response = await self.llm.chat(
            messages=[
                {"role": "system", "content": "You are a research assistant. Provide clear, organized summaries."},
                {"role": "user", "content": prompt},
            ],
        )

        content = response.get("message", {}).get("content", "")
        return content.strip()


def _has_tool_calls(response: dict) -> bool:
    message = response.get("message", {})
    tool_calls = message.get("tool_calls", [])
    return len(tool_calls) > 0


def _extract_tool_calls(response: dict) -> list[dict]:
    message = response.get("message", {})
    tool_calls = message.get("tool_calls", [])
    result = []
    for tc in tool_calls:
        func = tc.get("function", {})
        name = func.get("name", "")
        arguments = func.get("arguments", {})
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}
        result.append({"name": name, "arguments": arguments})
    return result