"""
Skill Tree Visualization component for DMlogn8n

This module provides visualization capabilities for skill trees,
progress tracking, and development analytics.
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import json
import math

from ..systems.skill_unlock_system import SkillTree, SkillNode
from ..core.skill import Skill, SkillCategory, MasteryLevel
from ..core.skill_progression import SkillProgression
from ..analyzers.performance_analyzer import PerformanceAnalyzer, PerformanceMetrics


class VisualizationFormat(Enum):
    """Supported visualization formats"""
    HTML = auto()
    JSON = auto()
    SVG = auto()
    D3_DATA = auto()
    MERMAID = auto()
    ASCII = auto()


@dataclass
class TreeNodeStyle:
    """Styling configuration for tree nodes"""
    size: Tuple[int, int] = (120, 80)  # width, height
    colors: Dict[str, str] = field(default_factory=lambda: {
        'locked': '#cccccc',
        'unlocked': '#4CAF50',
        'progress_25': '#FFC107',
        'progress_50': '#FF9800',
        'progress_75': '#FF5722',
        'mastery_novice': '#9E9E9E',
        'mastery_apprentice': '#2196F3',
        'mastery_journeyman': '#3F51B5',
        'mastery_expert': '#9C27B0',
        'mastery_master': '#F44336'
    })
    font_family: str = 'Arial, sans-serif'
    font_size: int = 12
    border_radius: int = 8
    show_progress: bool = True
    show_mastery: bool = True
    show_prerequisites: bool = True


@dataclass
class VisualizationOptions:
    """Options for skill tree visualization"""
    format: VisualizationFormat = VisualizationFormat.HTML
    node_style: TreeNodeStyle = field(default_factory=TreeNodeStyle)
    layout: str = 'hierarchical'  # 'hierarchical', 'radial', 'force'
    show_connections: bool = True
    show_labels: bool = True
    show_progress_bars: bool = True
    animate_transitions: bool = True
    include_analytics: bool = False
    responsive: bool = True
    theme: str = 'light'  # 'light', 'dark'


class SkillTreeVisualizer:
    """
    Comprehensive skill tree visualization system

    This class provides multiple visualization formats and styles for
    displaying skill trees, progress tracking, and development analytics.
    """

    def __init__(self, performance_analyzer: Optional[PerformanceAnalyzer] = None):
        self.performance_analyzer = performance_analyzer or PerformanceAnalyzer()
        self.default_options = VisualizationOptions()

    def visualize_tree(
        self,
        skill_tree: SkillTree,
        progression: SkillProgression,
        options: Optional[VisualizationOptions] = None
    ) -> Dict[str, Any]:
        """
        Generate visualization for a skill tree

        Args:
            skill_tree: The skill tree to visualize
            progression: Skill progression data
            options: Visualization options

        Returns:
            Dictionary containing visualization data
        """
        opts = options or self.default_options

        # Prepare node data
        nodes_data = self._prepare_nodes_data(skill_tree, progression, opts)

        # Prepare connections data
        connections_data = self._prepare_connections_data(skill_tree, opts)

        # Generate visualization based on format
        if opts.format == VisualizationFormat.HTML:
            return self._generate_html_visualization(nodes_data, connections_data, opts)
        elif opts.format == VisualizationFormat.JSON:
            return self._generate_json_visualization(nodes_data, connections_data, opts)
        elif opts.format == VisualizationFormat.SVG:
            return self._generate_svg_visualization(nodes_data, connections_data, opts)
        elif opts.format == VisualizationFormat.D3_DATA:
            return self._generate_d3_data(nodes_data, connections_data, opts)
        elif opts.format == VisualizationFormat.MERMAID:
            return self._generate_mermaid_diagram(nodes_data, connections_data, opts)
        elif opts.format == VisualizationFormat.ASCII:
            return self._generate_ascii_tree(skill_tree, progression, opts)
        else:
            raise ValueError(f"Unsupported visualization format: {opts.format}")

    def _prepare_nodes_data(
        self,
        skill_tree: SkillTree,
        progression: SkillProgression,
        options: VisualizationOptions
    ) -> List[Dict[str, Any]]:
        """Prepare node data for visualization"""
        nodes_data = []

        for node_name, node in skill_tree.nodes.items():
            # Get skill and performance data
            skill = node.skill
            performance = None
            if skill and self.performance_analyzer:
                performance = self.performance_analyzer.analyze_skill_performance(skill, progression)

            # Calculate node color based on state
            color = self._get_node_color(node, skill, options.node_style)

            # Prepare node data
            node_data = {
                'id': node_name,
                'name': skill.name if skill else node_name,
                'category': skill.category.value if skill else 'UNKNOWN',
                'position': node.position,
                'color': color,
                'unlocked': node.unlocked,
                'is_root': node.is_root,
                'size': options.node_style.size,
                'requirements': self._format_requirements(node.requirements),
                'description': skill.description if skill else '',
            }

            # Add mastery level information
            if skill:
                node_data.update({
                    'mastery_level': skill.current_level.name,
                    'mastery_color': options.node_style.colors.get(f'mastery_{skill.current_level.name.lower()}', '#cccccc'),
                    'total_xp': skill.total_xp,
                    'xp_to_next': skill.xp_to_next_level,
                    'success_rate': skill.success_rate,
                    'total_uses': skill.total_uses
                })

            # Add performance metrics if available
            if performance:
                node_data.update({
                    'effectiveness_score': performance.effectiveness_score,
                    'performance_tier': performance.performance_tier.name,
                    'trend_direction': performance.trend_direction.name,
                    'usage_frequency': performance.usage_frequency
                })

            # Add progress information
            if not node.unlocked and skill:
                progress = skill_tree.get_skill_progress(node_name, progression)
                node_data['progress_percentage'] = progress.get('progress_percentage', 0)

            nodes_data.append(node_data)

        return nodes_data

    def _prepare_connections_data(
        self,
        skill_tree: SkillTree,
        options: VisualizationOptions
    ) -> List[Dict[str, Any]]:
        """Prepare connection data for visualization"""
        connections_data = []

        for node_name, node in skill_tree.nodes.items():
            for child_name in node.child_nodes:
                if child_name in skill_tree.nodes:
                    child_node = skill_tree.nodes[child_name]
                    connections_data.append({
                        'from': node_name,
                        'to': child_name,
                        'from_position': node.position,
                        'to_position': child_node.position,
                        'type': 'prerequisite' if not node.unlocked else 'active',
                        'strength': 1.0
                    })

        return connections_data

    def _get_node_color(self, node: SkillNode, skill: Optional[Skill], style: TreeNodeStyle) -> str:
        """Get appropriate color for a node based on its state"""
        if node.unlocked:
            if skill:
                return style.colors.get(f'mastery_{skill.current_level.name.lower()}', style.colors['unlocked'])
            return style.colors['unlocked']

        # For locked nodes, show progress
        if skill and skill.total_xp > 0:
            progress_percentage = (skill.total_xp / skill.xp_to_next_level) * 100 if skill.xp_to_next_level > 0 else 0
            if progress_percentage >= 75:
                return style.colors['progress_75']
            elif progress_percentage >= 50:
                return style.colors['progress_50']
            elif progress_percentage >= 25:
                return style.colors['progress_25']

        return style.colors['locked']

    def _format_requirements(self, requirements: List) -> List[str]:
        """Format requirements for display"""
        formatted = []
        for req in requirements:
            if hasattr(req, 'description'):
                formatted.append(req.description)
            else:
                formatted.append(str(req))
        return formatted

    def _generate_html_visualization(
        self,
        nodes_data: List[Dict[str, Any]],
        connections_data: List[Dict[str, Any]],
        options: VisualizationOptions
    ) -> Dict[str, Any]:
        """Generate HTML visualization with D3.js"""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Skill Tree Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: {font_family};
            margin: 0;
            padding: 20px;
            background-color: {bg_color};
        }}
        .node {{
            stroke: #333;
            stroke-width: 2px;
            cursor: pointer;
        }}
        .node-label {{
            font-size: {font_size}px;
            text-anchor: middle;
            pointer-events: none;
        }}
        .link {{
            stroke: #999;
            stroke-width: 2px;
            fill: none;
            marker-end: url(#arrowhead);
        }}
        .tooltip {{
            position: absolute;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
        }}
        .progress-bar {{
            height: 4px;
            background: #ddd;
            border-radius: 2px;
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            background: #4CAF50;
            transition: width 0.3s ease;
        }}
    </style>
</head>
<body>
    <svg id="skill-tree" width="1200" height="800"></svg>
    <div class="tooltip"></div>

    <script>
        // Data
        const nodes = {nodes_data};
        const links = {connections_data};

        // Create SVG
        const svg = d3.select("#skill-tree");
        const width = +svg.attr("width");
        const height = +svg.attr("height");

        // Create arrow marker
        svg.append("defs").append("marker")
            .attr("id", "arrowhead")
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 15)
            .attr("refY", 0)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("fill", "#999");

        // Create force simulation
        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(150))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(80));

        // Create links
        const link = svg.append("g")
            .selectAll("line")
            .data(links)
            .enter().append("line")
            .attr("class", "link");

        // Create nodes
        const node = svg.append("g")
            .selectAll("g")
            .data(nodes)
            .enter().append("g")
            .attr("class", "node")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        // Add rectangles for nodes
        node.append("rect")
            .attr("width", d => d.size[0])
            .attr("height", d => d.size[1])
            .attr("x", d => -d.size[0] / 2)
            .attr("y", d => -d.size[1] / 2)
            .attr("rx", 8)
            .attr("fill", d => d.color);

        // Add progress bars
        node.filter(d => d.progress_percentage !== undefined)
            .append("rect")
            .attr("class", "progress-bar")
            .attr("width", d => d.size[0] - 10)
            .attr("height", 4)
            .attr("x", d => -d.size[0] / 2 + 5)
            .attr("y", d => d.size[1] / 2 - 10)
            .attr("fill", "#ddd");

        node.filter(d => d.progress_percentage !== undefined)
            .append("rect")
            .attr("class", "progress-fill")
            .attr("width", d => (d.size[0] - 10) * (d.progress_percentage / 100))
            .attr("height", 4)
            .attr("x", d => -d.size[0] / 2 + 5)
            .attr("y", d => d.size[1] / 2 - 10);

        // Add labels
        node.append("text")
            .attr("class", "node-label")
            .attr("dy", -5)
            .text(d => d.name.length > 15 ? d.name.substring(0, 12) + "..." : d.name);

        node.append("text")
            .attr("class", "node-label")
            .attr("dy", 10)
            .attr("font-size", "10px")
            .attr("fill", "#666")
            .text(d => d.mastery_level || "");

        // Add tooltips
        const tooltip = d3.select(".tooltip");

        node.on("mouseover", function(event, d) {{
            tooltip.transition().duration(200).style("opacity", .9);
            tooltip.html(`
                <strong>${{d.name}}</strong><br/>
                Category: ${{d.category}}<br/>
                ${{'Level: ' + d.mastery_level + '<br/>' if d.mastery_level else ''}}
                ${{'XP: ' + d.total_xp + '<br/>' if d.total_xp !== undefined else ''}}
                ${{'Success Rate: ' + d.success_rate.toFixed(1) + '%<br/>' if d.success_rate !== undefined else ''}}
                ${{'Progress: ' + d.progress_percentage.toFixed(1) + '%<br/>' if d.progress_percentage !== undefined else ''}}
                ${{'Requirements:<br/>' + d.requirements.join('<br/>') if d.requirements && d.requirements.length > 0 else ''}}
            `)
            .style("left", (event.pageX + 10) + "px")
            .style("top", (event.pageY - 28) + "px");
        }})
        .on("mouseout", function(d) {{
            tooltip.transition().duration(500).style("opacity", 0);
        }});

        // Update positions on simulation tick
        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
        }});

        // Drag functions
        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}

        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}

        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}
    </script>
</body>
</html>
        """

        bg_color = '#f5f5f5' if options.theme == 'light' else '#1a1a1a'
        text_color = '#333333' if options.theme == 'light' else '#ffffff'

        return {
            'format': 'html',
            'content': html_template.format(
                font_family=options.node_style.font_family,
                font_size=options.node_style.font_size,
                bg_color=bg_color,
                nodes_data=json.dumps(nodes_data),
                connections_data=json.dumps(connections_data)
            ),
            'nodes_count': len(nodes_data),
            'connections_count': len(connections_data)
        }

    def _generate_json_visualization(
        self,
        nodes_data: List[Dict[str, Any]],
        connections_data: List[Dict[str, Any]],
        options: VisualizationOptions
    ) -> Dict[str, Any]:
        """Generate JSON visualization data"""
        return {
            'format': 'json',
            'options': {
                'layout': options.layout,
                'show_connections': options.show_connections,
                'show_labels': options.show_labels,
                'theme': options.theme
            },
            'nodes': nodes_data,
            'connections': connections_data,
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_nodes': len(nodes_data),
                'total_connections': len(connections_data)
            }
        }

    def _generate_svg_visualization(
        self,
        nodes_data: List[Dict[str, Any]],
        connections_data: List[Dict[str, Any]],
        options: VisualizationOptions
    ) -> Dict[str, Any]:
        """Generate static SVG visualization"""
        # Simple hierarchical layout
        svg_elements = []
        width, height = 1200, 800

        # Calculate positions if not provided
        if options.layout == 'hierarchical':
            self._calculate_hierarchical_layout(nodes_data, connections_data, width, height)

        # Add connections
        for connection in connections_data:
            from_pos = connection['from_position']
            to_pos = connection['to_position']
            svg_elements.append(
                f'<line x1="{from_pos[0]}" y1="{from_pos[1]}" '
                f'x2="{to_pos[0]}" y2="{to_pos[1]}" '
                f'stroke="#999" stroke-width="2" marker-end="url(#arrowhead)"/>'
            )

        # Add nodes
        for node in nodes_data:
            x, y = node['position']
            w, h = node['size']
            svg_elements.append(
                f'<rect x="{x - w/2}" y="{y - h/2}" width="{w}" height="{h}" '
                f'fill="{node["color"]}" stroke="#333" stroke-width="2" rx="8"/>'
            )
            svg_elements.append(
                f'<text x="{x}" y="{y}" text-anchor="middle" '
                f'font-family="{options.node_style.font_family}" '
                f'font-size="{options.node_style.font_size}">{node["name"]}</text>'
            )

        svg_content = f"""
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <marker id="arrowhead" markerWidth="10" markerHeight="7"
                refX="9" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#999" />
        </marker>
    </defs>
    {''.join(svg_elements)}
</svg>
        """

        return {
            'format': 'svg',
            'content': svg_content,
            'nodes_count': len(nodes_data),
            'connections_count': len(connections_data)
        }

    def _generate_d3_data(
        self,
        nodes_data: List[Dict[str, Any]],
        connections_data: List[Dict[str, Any]],
        options: VisualizationOptions
    ) -> Dict[str, Any]:
        """Generate D3.js compatible data structure"""
        # Transform connections to D3 link format
        links = []
        for connection in connections_data:
            links.append({
                'source': connection['from'],
                'target': connection['to'],
                'value': connection.get('strength', 1)
            })

        return {
            'format': 'd3_data',
            'nodes': nodes_data,
            'links': links,
            'options': {
                'layout': options.layout,
                'theme': options.theme
            }
        }

    def _generate_mermaid_diagram(
        self,
        nodes_data: List[Dict[str, Any]],
        connections_data: List[Dict[str, Any]],
        options: VisualizationOptions
    ) -> Dict[str, Any]:
        """Generate Mermaid diagram syntax"""
        lines = ['graph TD']

        # Add nodes
        for node in nodes_data:
            node_id = node['id'].replace(' ', '_').replace('-', '_')
            label = node['name']
            if node.get('mastery_level'):
                label += f'\\n({node["mastery_level"]})'

            color = node['color']
            lines.append(f'    {node_id}["{label}"]:::node{node_id}')

        # Add connections
        for connection in connections_data:
            from_id = connection['from'].replace(' ', '_').replace('-', '_')
            to_id = connection['to'].replace(' ', '_').replace('-', '_')
            lines.append(f'    {from_id} --> {to_id}')

        # Add styles
        lines.append('')
        for node in nodes_data:
            node_id = node['id'].replace(' ', '_').replace('-', '_')
            lines.append(f'    classDef node{node_id} fill:{node["color"]},stroke:#333,stroke-width:2px')

        mermaid_code = '\n'.join(lines)

        return {
            'format': 'mermaid',
            'content': mermaid_code,
            'nodes_count': len(nodes_data),
            'connections_count': len(connections_data)
        }

    def _generate_ascii_tree(
        self,
        skill_tree: SkillTree,
        progression: SkillProgression,
        options: VisualizationOptions
    ) -> Dict[str, Any]:
        """Generate ASCII art tree representation"""
        lines = []

        # Find root nodes
        root_nodes = [name for name in skill_tree.root_nodes if name in skill_tree.nodes]

        for root_name in root_nodes:
            lines.append(self._generate_ascii_node(skill_tree, progression, root_name, "", True))

        ascii_content = '\n'.join(lines)

        return {
            'format': 'ascii',
            'content': ascii_content,
            'nodes_count': len(skill_tree.nodes)
        }

    def _generate_ascii_node(
        self,
        skill_tree: SkillTree,
        progression: SkillProgression,
        node_name: str,
        prefix: str,
        is_last: bool
    ) -> str:
        """Generate ASCII representation for a single node and its children"""
        node = skill_tree.nodes[node_name]
        skill = node.skill

        # Node symbol based on state
        if node.unlocked:
            symbol = "✓"
        elif skill and skill.total_xp > 0:
            symbol = "◐"
        else:
            symbol = "○"

        # Format node line
        connector = "└── " if is_last else "├── "
        node_line = f"{prefix}{connector}{symbol} {node_name}"

        if skill:
            node_line += f" ({skill.current_level.name})"
            if skill.total_xp > 0:
                node_line += f" [{skill.total_xp} XP]"

        lines = [node_line]

        # Add children
        children = node.child_nodes
        for i, child_name in enumerate(children):
            if child_name in skill_tree.nodes:
                child_prefix = prefix + ("    " if is_last else "│   ")
                child_is_last = (i == len(children) - 1)
                child_ascii = self._generate_ascii_node(
                    skill_tree, progression, child_name, child_prefix, child_is_last
                )
                lines.append(child_ascii)

        return '\n'.join(lines)

    def _calculate_hierarchical_layout(
        self,
        nodes_data: List[Dict[str, Any]],
        connections_data: List[Dict[str, Any]],
        width: int,
        height: int
    ) -> None:
        """Calculate hierarchical layout positions"""
        # Build adjacency lists
        children = {node['id']: [] for node in nodes_data}
        parents = {node['id']: [] for node in nodes_data}

        for connection in connections_data:
            parent = connection['from']
            child = connection['to']
            children[parent].append(child)
            parents[child].append(parent)

        # Find root nodes (no parents)
        roots = [node_id for node_id, parent_list in parents.items() if not parent_list]

        # Assign levels using BFS
        levels = {}
        queue = [(root, 0) for root in roots]
        while queue:
            node_id, level = queue.pop(0)
            if node_id not in levels:
                levels[node_id] = level
                for child in children[node_id]:
                    queue.append((child, level + 1))

        # Group nodes by level
        level_groups = {}
        for node_id, level in levels.items():
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(node_id)

        # Assign positions
        level_height = height / (max(levels.values()) + 1)
        for level, node_ids in level_groups.items():
            y = (level + 1) * level_height
            level_width = width / (len(node_ids) + 1)
            for i, node_id in enumerate(node_ids):
                x = (i + 1) * level_width
                # Update node position
                for node in nodes_data:
                    if node['id'] == node_id:
                        node['position'] = (x, y)
                        break

    def export_visualization(
        self,
        visualization_data: Dict[str, Any],
        filename: str
    ) -> bool:
        """Export visualization to file"""
        try:
            format_type = visualization_data.get('format', 'json')
            content = visualization_data.get('content', visualization_data)

            if format_type == 'json':
                with open(filename, 'w') as f:
                    json.dump(content, f, indent=2)
            else:
                with open(filename, 'w') as f:
                    if isinstance(content, str):
                        f.write(content)
                    else:
                        json.dump(content, f, indent=2)

            return True
        except Exception as e:
            print(f"Error exporting visualization: {e}")
            return False