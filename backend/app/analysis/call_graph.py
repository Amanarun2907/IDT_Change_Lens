from typing import List, Dict, Any, Tuple
from app.models.schemas import ImpactItem, ImpactGraph, GraphNode, GraphEdge, BlastRadius

class CallGraphBuilder:
    """
    Constructs React Flow graph visualization (nodes & edges)
    and estimates blast radius based on topological reachability.
    """

    @staticmethod
    def build_graph_and_blast_radius(impact_items: List[ImpactItem]) -> Tuple[ImpactGraph, BlastRadius, str]:
        nodes_dict: Dict[str, GraphNode] = {}
        edges: List[GraphEdge] = []

        total_callers = 0
        distinct_modules = set()

        for item in impact_items:
            # Node for the modified symbol
            sym_id = f"mod_{item.modified_symbol}"
            if sym_id not in nodes_dict:
                nodes_dict[sym_id] = GraphNode(
                    id=sym_id,
                    label=f"{item.modified_symbol}()",
                    type="FUNCTION" if item.symbol_type == "function" else "CLASS",
                    severity="HIGH" if item.affected_apis else "MEDIUM",
                    status="MODIFIED",
                    details={
                        "file": item.file_path,
                        "type": item.symbol_type,
                        "impact_type": item.impact_type
                    }
                )

            # Node for the file container
            file_id = f"file_{item.file_path}"
            if file_id not in nodes_dict:
                nodes_dict[file_id] = GraphNode(
                    id=file_id,
                    label=item.file_path,
                    type="FILE",
                    status="MODIFIED",
                    details={"file": item.file_path}
                )
            edges.append(GraphEdge(
                id=f"e_{file_id}_{sym_id}",
                source=file_id,
                target=sym_id,
                label="defines",
                relationship="EXPOSES",
                verified=True
            ))

            # Nodes for callers
            for caller in item.direct_callers:
                total_callers += 1
                caller_id = f"caller_{caller}"
                if caller_id not in nodes_dict:
                    nodes_dict[caller_id] = GraphNode(
                        id=caller_id,
                        label=caller.split("/")[-1],
                        type="FILE",
                        status="CALLER",
                        details={"file": caller}
                    )
                edges.append(GraphEdge(
                    id=f"e_{caller_id}_{sym_id}",
                    source=caller_id,
                    target=sym_id,
                    label="invokes",
                    relationship="CALLS",
                    verified=item.verified
                ))

            # Nodes for affected APIs
            for api in item.affected_apis:
                api_id = f"api_{api}"
                if api_id not in nodes_dict:
                    nodes_dict[api_id] = GraphNode(
                        id=api_id,
                        label=f"API: {api.split('/')[-1]}",
                        type="API",
                        severity="CRITICAL",
                        status="DEPENDENT",
                        details={"file": api}
                    )
                edges.append(GraphEdge(
                    id=f"e_{sym_id}_{api_id}",
                    source=sym_id,
                    target=api_id,
                    label="powers",
                    relationship="DEPENDS_ON",
                    verified=True
                ))

            for mod in item.dependent_modules:
                distinct_modules.add(mod)

        # Blast Radius classification
        if len(distinct_modules) >= 3 or total_callers >= 6 or any(item.affected_apis for item in impact_items):
            blast_radius = BlastRadius.APPLICATION_WIDE
            explanation = f"Changes propagate across {len(distinct_modules)} modules and affect {total_callers} callers including exposed API endpoints."
        elif len(distinct_modules) >= 2 or total_callers >= 3:
            blast_radius = BlastRadius.CROSS_MODULE
            explanation = f"Changes propagate across {len(distinct_modules)} modules with {total_callers} direct callers."
        elif total_callers >= 1:
            blast_radius = BlastRadius.MODULE_LEVEL
            explanation = f"Impact is confined to {total_callers} callers within the same subsystem."
        else:
            blast_radius = BlastRadius.LOCALIZED
            explanation = "Changes are self-contained with no detected external callers or dependent API endpoints."

        impact_graph = ImpactGraph(
            nodes=list(nodes_dict.values()),
            edges=edges
        )

        return impact_graph, blast_radius, explanation
