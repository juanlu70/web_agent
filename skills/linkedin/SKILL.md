---
name: linkedin
description: "Search Linkedin and extract information from search results. Use when: user asks to search for information on any topic on Linkedin explicity, find jobs and candidates, read job descriptions and job experience, don't look on postings. NOT for: direct URL access (use web_fetch)."
website_url: "https://www.linkedin.com"
---

# Linkedin Search Skill

Search Linkedin and extract information from jobs and people that are possible candidates for a job.

## When to Use

- User asks to search for information from Linkedin
- Need to find jobs or candidates related to a topic
- Research tasks to get the most closesest offers and candidates related with the search topic.

## When NOT to Use

- Accessing Linkedin directly (use web_fetch)
- Non Linkedin related search (use browser)
- Local file operations

## Instructions when searching only for jobs

1. Use the `web_search` tool with focus on Europe, Switzerland, UK and Spain (all are valid) for specific query.
2. Use `web_fetch` on the most relevant results to extract content
4. Summarize findings and cite sources, extract ALL links to job offers.
5. If you can't access job offers or can't access candidate profiles, please notify in the log in uppercase!
6. Discard all jobs that can't be done remote from Spain, if it says [country] based, discard it unless the country is Spain.
7. When looking for jobs, you must list only contract, Past 24 hours and Remote.
8. In the URL: `f_JT=C` filters for Contract, `f_TPR=r86400` filters for Past 24 Hours, and `f_WRA=true` filters for Remote
9. **Use the Salary Filter:** On the right side of the search results page, look for the **Salary** filter. You can set a minimum baseline $70k+ annually, or equivalent high hourly rates for contracts.
10. **Filter by Experience Level:** Use the **Experience Level** filter on the right-hand side and select **Mid-Senior** and **Senior**. Higher experience levels typically correlate with higher-paying contracts.
11. **Sort by Date:** Ensure the results are sorted by **"Most recent"** rather than "Relevance" so you only see the freshest postings from the last 24 hours.
12. Show all the job links in the answer, wether you can access the link or not.

## Instructions when searching for candidates

1. Never search on Linkedin for candidates, other websites are valid.
2. Define a string to search, for example: (java developer OR java backend) AND (j2ee OR spring).
3. Add a location if the job offer is on-site of hybrid, for example: Madrid.
4. Search in Google and look for the previous items and add the final words: #OpenToWork site:linkedin.com if you want candidates.
5. Show all the links to candidates in the answer, wether you can access the link or not.

## Search Tips

- Don't consume URLs too much fast, take pauses, so Linkedin will not know that you are a robot.
- Act like as a human being, take simulated human pauses to read jobs and descriptions.
- The tool returns up to 10 results maximum, until the --deep flag is activated, then 50 results.
- Always extract content from promising results before summarizing.

