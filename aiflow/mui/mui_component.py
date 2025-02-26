from typing import Any, Dict, List, Optional, Union
import time

class MUIComponent:
    _sent_components = {}

    def __init__(
        self,
        type_name: str,
        module: str = "muiElements",
        props: Optional[Dict[str, Any]] = None,
        children: Optional[List[Union[str, "MUIComponent"]]] = None,
        builder: Optional[Any] = None
    ):
        self.type = "text" if module == "text" else type_name
        self.module = module
        self.props = props or {}
        self.children = []
        self._builder = builder
        self._parent = None
        self.unique_id = self._builder.get_next_id() if self._builder else 0
        self.text_content = None
        self._child_components = []
        self._parent_id = None
        self._is_prop_component = False
        self._prop_parent = None

        # Handle text content
        if module == "text" or (children and len(children) == 1 and isinstance(children[0], (str, int, float))):
            self.text_content = str(type_name if module == "text" else children[0])
        elif children:
            self._process_children(children)

    def _process_children(self, children):
        for idx, child in enumerate(children):
            if isinstance(child, (str, int, float)):
                self.children.append({
                    "type": "text",
                    "content": str(child),
                    "id": f"text_{self.unique_id}_{len(self.children)}"
                })
            else:
                self.children.append(child)

    def _process_props(self) -> Dict[str, Any]:
        processed_props = {}
        for key, value in self.props.items():
            if isinstance(value, MUIComponent):
                # Set the parent for prop components
                value._parent = self
                value._is_prop_component = True
                processed_props[key] = value.to_dict()
            else:
                processed_props[key] = value
        return processed_props

    def __enter__(self):
        if hasattr(self, '_is_prop'):
            return self

        component_data = self._create_component_data()
        
        if self._builder:
            self._builder._stack.append(self)
        return self

    def _create_component_data(self) -> Dict[str, Any]:
        component_id = f"{self.type}_{self.unique_id}"
        parent_id = None
        
        if self._parent:
            parent_id = f"{self._parent.type}_{self._parent.unique_id}"
            
        data = {
            "type": self.type,
            "id": component_id,
            "module": self.module,
            "props": self._process_props(),
            "parentId": parent_id,
            "children": []
        }

        if self.text_content is not None:
            data["content"] = self.text_content

        if self.children:
            for child in self.children:
                if isinstance(child, dict) and child["type"] == "text":
                    child_data = {
                        "type": "text",
                        "id": f"text_{self.unique_id}_{len(data['children'])}",
                        "content": child["content"],
                        "parentId": component_id
                    }
                    data["children"].append(child_data)
                elif isinstance(child, MUIComponent):
                    child._parent = self
                    child_data = child.to_dict()
                    child_data["parentId"] = component_id
                    data["children"].append(child_data)

        return data

    def add_child(self, child: "MUIComponent") -> None:
        child._parent = self
        self._child_components.append(child)
        if child not in self.children:
            self.children.append(child)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._builder and self._builder._stack:
            if len(self._builder._stack) > 1:
                current = self._builder._stack.pop()
                parent = self._builder._stack[-1]
                current._parent = parent
                if current not in parent.children:
                    parent.children.append(current)
            else:
                self._builder.root = self._builder._stack.pop()
        return False

    def to_dict(self) -> Dict[str, Any]:
        component_id = f"{self.type}_{self.unique_id}"
        parent_id = None
        
        if self._parent:
            # Use immediate parent for prop components
            parent_id = f"{self._parent.type}_{self._parent.unique_id}"
            
        data = {
            "type": self.type,
            "id": component_id,
            "module": self.module,
            "props": self._process_props(),
            "parentId": parent_id
        }
        
        if self.text_content is not None:
            data["content"] = self.text_content
            
        return data
