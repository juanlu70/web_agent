---
name: web_agent.py
description: A browser agent managed by the IA made in python
---


# Description

This is a project to create a main orchestrator agent that creates another agents to browse the web and extract information.

For make this project you must review the openclaw project (already downloaded on this directory) and learn how the webs browser works, then copy the mechanism of web browsing and add to this project, this will be the central spine of this project, later we will add more features.

The main agent will receive a request, maybe from command-line or from a web form, possibly streamlit, it will create a new agent to browse the web to fulfill the request sent to the main orchestrator agent.

The child agent will have a markdown file as a MCP, or a skill markdown for connecting certain websites and help the browsing around certain websites, so it does not have to learn how they work again.

I want that each agent work as a parallel process, leving the main process listening for new requests, also a subagent could create more subagents working all the same to make the work faster if the task requires it.


# Input

1.- A request from a client program or command-line.
2.- Main orchestrator agent plans how do the task depending of it.
3.- The orchestrator spread one or more agents to make the task and receive the feedback from subagent/s.
4.- The orchestrator answers the client.


# Output

Usually the result would be a resume of all the information gathered, unless the client ask for details, that will be shown to the client.


# Constraints

- Don't take decisions for yourself, maybe you will have doubts or ignore the correct answer for some problem, ask always before developing a solution. I knwo there will be lots of details that I forgot to specify here.
- The program must be done in python using the most recent technology and looking at solutions on openclaw source code downloaded on this directory.
- The main work of this program is to search the web and gather the maximum information as possible.
- If you have to make some work learning how to browse certain website, write a skill markdown file and store it on skills directory for use later.
- If you search on the web, use Google as search engine, and don't take more than the first 10 results.
- You are fully autonomous, you can learn surfing the web, if don't know anything notify it to the user and the first thing to do is to gather information to learn how to do it, once learned, write a skill markdown file in skills directory.


