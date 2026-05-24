from langgraph.graph import StateGraph, START, END
from app.models.state import JobApplicationState
from app.agents.job_fetcher_agent import job_fetcher_agent
from app.agents.criteria_matcher_agent import criteria_matcher_agent
from app.agents.job_applier_agent import job_applier_agent

graph = StateGraph(JobApplicationState)

graph.add_node("fetcher", job_fetcher_agent)
graph.add_node("filter", criteria_matcher_agent)
graph.add_node("applier", job_applier_agent)

graph.add_edge(START, "fetcher")
graph.add_edge("fetcher", "filter")
graph.add_edge("filter", "applier")
graph.add_edge("applier", END)

job_graph = graph.compile()
