"""
Workflow processor implementing rgthree's "Queue Selected Output Nodes" algorithm.

This module provides functionality to create minimal workflows by selecting specific
output nodes and including only their dependencies, optimizing execution time and resources.
"""

import copy
from typing import Dict, List, Any, Set, Optional


class WorkflowProcessor:
    """
    Processes ComfyUI workflows to create minimal execution graphs.
    
    Based on the rgthree "Queue Selected Output Nodes" algorithm that allows
    executing only selected output nodes and their dependencies.
    """
    
    def __init__(self):
        self.visited_nodes: Set[str] = set()
    
    def is_output_node(self, node_data: Dict[str, Any]) -> bool:
        """
        Determines if a node is an output node.
        
        Args:
            node_data: Node data from the workflow
            
        Returns:
            True if the node is an output node
        """
        class_type = node_data.get('class_type', '')
        
        # Common output node types in ComfyUI
        output_node_types = [
            'SaveImage',
            'PreviewImage', 
            'SaveVideo',
            'SaveGIF',
            'VHS_VideoCombine',
            'SaveAnimatedWEBP',
            'SaveAnimatedPNG',
            'DisplayText',
            'ShowText',
            'PrintText',
            # Add more output node types as needed
        ]
        
        # Check if explicitly marked as output node or matches known types
        is_explicit_output = node_data.get('_meta', {}).get('output_node', False)
        is_known_output_type = class_type in output_node_types
        
        return is_explicit_output or is_known_output_type
    
    def get_output_nodes(self, workflow: Dict[str, Any], selected_node_ids: List[str] = None) -> List[str]:
        """
        Gets list of output node IDs from workflow.
        
        Args:
            workflow: Full ComfyUI workflow
            selected_node_ids: List of selected nodes (optional)
            
        Returns:
            List of output node IDs
        """
        output_nodes = []
        
        nodes_to_check = selected_node_ids if selected_node_ids else workflow.keys()
        
        for node_id in nodes_to_check:
            if node_id in workflow:
                node_data = workflow[node_id]
                if self.is_output_node(node_data):
                    output_nodes.append(node_id)
                    
        return output_nodes
    
    def recursive_add_nodes(self, node_id: str, old_workflow: Dict[str, Any], 
                          new_workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively adds a node and all its dependencies to the new workflow.
        
        Args:
            node_id: ID of the current node
            old_workflow: Original full workflow
            new_workflow: New trimmed workflow
            
        Returns:
            Updated new workflow
        """
        # Skip if node already processed
        if node_id in new_workflow or node_id in self.visited_nodes:
            return new_workflow
            
        # Check if node exists
        if node_id not in old_workflow:
            print(f"Warning: Node {node_id} not found in workflow")
            return new_workflow
            
        # Mark node as visited
        self.visited_nodes.add(node_id)
        current_node = old_workflow[node_id]
        
        # Copy node to new workflow
        new_workflow[node_id] = copy.deepcopy(current_node)
        
        # Process all node inputs
        inputs = current_node.get('inputs', {})
        
        for input_name, input_value in inputs.items():
            # Check if input is a connection to another node
            if isinstance(input_value, list) and len(input_value) >= 2:
                # input_value format: [node_id, output_slot]
                connected_node_id = str(input_value[0])
                
                # Recursively add dependency node
                self.recursive_add_nodes(connected_node_id, old_workflow, new_workflow)
        
        return new_workflow
    
    def create_minimal_workflow(self, full_workflow: Dict[str, Any], 
                              output_node_ids: List[str]) -> Dict[str, Any]:
        """
        Creates minimal workflow containing only selected output nodes and their dependencies.
        
        Args:
            full_workflow: Full original workflow
            output_node_ids: List of output node IDs to execute
            
        Returns:
            Trimmed workflow
        """
        # Reset state
        self.visited_nodes.clear()
        
        # Create new empty workflow
        minimal_workflow = {}
        
        # For each selected output node, add it and all dependencies
        for output_node_id in output_node_ids:
            self.recursive_add_nodes(output_node_id, full_workflow, minimal_workflow)
            
        return minimal_workflow
    
    def process_workflow_for_output_nodes(self, full_workflow: Dict[str, Any], 
                                        selected_node_ids: List[str]) -> Dict[str, Any]:
        """
        Main function implementing rgthree's "Queue Selected Output Nodes" algorithm.
        
        Args:
            full_workflow: Full ComfyUI workflow
            selected_node_ids: List of selected node IDs
            
        Returns:
            Trimmed workflow for execution
        """
        # Step 1: Find output nodes among selected
        output_nodes = self.get_output_nodes(full_workflow, selected_node_ids)
        
        if not output_nodes:
            raise ValueError("No output nodes found among selected nodes")
        
        # Step 2: Create minimal workflow
        minimal_workflow = self.create_minimal_workflow(full_workflow, output_nodes)
        
        return minimal_workflow
    
    def get_workflow_statistics(self, original_workflow: Dict[str, Any], 
                              minimal_workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns statistics about workflow optimization.
        
        Args:
            original_workflow: Original full workflow
            minimal_workflow: Trimmed workflow
            
        Returns:
            Dictionary with statistics
        """
        original_count = len(original_workflow)
        minimal_count = len(minimal_workflow)
        saved_count = original_count - minimal_count
        saved_percentage = (saved_count / original_count * 100) if original_count > 0 else 0
        
        return {
            "original_nodes": original_count,
            "minimal_nodes": minimal_count,
            "saved_nodes": saved_count,
            "saved_percentage": saved_percentage
        }