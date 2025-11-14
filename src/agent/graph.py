"""LangGraph Workflow Graph Definition"""
from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import (
    input_node,
    identify_measures_node,
    rewrite_query_node,
    human_review_node1,
    json_lookup_node,
    sql_generation_node,
    human_review_node2,
    execute_and_export_node
)


def create_workflow() -> StateGraph:
    """
    Create and configure the LangGraph workflow

    Returns:
        Compiled StateGraph workflow
    """
    # Create the graph
    workflow = StateGraph(AgentState)

    # Add all nodes
    workflow.add_node("input", input_node)
    workflow.add_node("identify", identify_measures_node)
    workflow.add_node("rewrite", rewrite_query_node)
    workflow.add_node("review1", human_review_node1)
    workflow.add_node("json_lookup", json_lookup_node)
    workflow.add_node("generate_sql", sql_generation_node)
    workflow.add_node("review2", human_review_node2)
    workflow.add_node("execute", execute_and_export_node)

    # Set entry point
    workflow.set_entry_point("input")

    # Add sequential edges
    workflow.add_edge("input", "identify")
    workflow.add_edge("identify", "rewrite")
    workflow.add_edge("rewrite", "review1")
    workflow.add_edge("review1", "json_lookup")

    # Conditional edge after json_lookup (check for errors)
    def check_json_lookup_error(state: AgentState) -> str:
        """Check if JSON lookup found an error"""
        if state.get("error"):
            return "error"
        return "continue"

    workflow.add_conditional_edges(
        "json_lookup",
        check_json_lookup_error,
        {
            "error": END,
            "continue": "generate_sql"
        }
    )

    # Add edge from generate_sql to review2
    workflow.add_edge("generate_sql", "review2")

    # Conditional edge after review2 (check if SQL review is enabled)
    # Note: In practice, review2 node handles the conditional logic internally
    # We just need to route to execute or END based on errors
    def check_sql_generation_error(state: AgentState) -> str:
        """Check if SQL generation found an error"""
        if state.get("error"):
            return "error"
        return "execute"

    workflow.add_conditional_edges(
        "review2",
        check_sql_generation_error,
        {
            "error": END,
            "execute": "execute"
        }
    )

    # Final edge to END
    workflow.add_edge("execute", END)

    # Compile the graph
    compiled_workflow = workflow.compile()

    return compiled_workflow


def run_workflow(initial_state: AgentState) -> AgentState:
    """
    Run the workflow with an initial state

    Args:
        initial_state: Initial agent state

    Returns:
        Final agent state after workflow completion
    """
    workflow = create_workflow()

    # Run the workflow
    final_state = workflow.invoke(initial_state)

    return final_state


def visualize_workflow(output_path: str = "workflow_graph.png"):
    """
    Visualize the workflow graph and save to file

    Args:
        output_path: Path to save the visualization
    """
    try:
        from IPython.display import Image, display
        workflow = create_workflow()

        # Get the graph visualization
        graph_image = workflow.get_graph().draw_mermaid_png()

        # Save to file
        with open(output_path, 'wb') as f:
            f.write(graph_image)

        print(f"Workflow graph saved to {output_path}")

        # Display if in Jupyter
        try:
            display(Image(graph_image))
        except:
            pass

    except Exception as e:
        print(f"Could not visualize workflow: {e}")
        print("Note: Visualization requires graphviz and IPython")
