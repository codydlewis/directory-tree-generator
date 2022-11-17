"""
# Directory tree structure (dirtree)

This project provides code to convert a directory tree structure (defined in a
JSON file) into an actual directory tree at a defined location on your
computer.
"""

from __future__ import annotations
import os
from typing import Optional, Union, List, Dict
import json


class Directory:
    """
    Directory objects represent digital 'folders' which contain other folders
    and files.
    """

    def __init__(
        self, name: str, description: str = Optional[str], icon: str = "folder"
    ) -> None:
        self._name = name
        self.description = description
        self.icon = icon
        self._parent = None
        self._children = []

    def __repr__(self) -> str:
        return f"Directory('{self.name}', {len(self._children)} children)"

    def __getitem__(self, key: str) -> Directory:
        """Get child Directory object by `name` attibute of children.
        Guaranteed unique."""

        for child in self._children:
            if child.name == key:
                return child
        raise KeyError(
            f"No subdirectory has the name "
            f"'{key}' in '{self.name}'"
        )

    @staticmethod
    def _tree_builder(obj: Dict, /) -> Directory:
        """Recursively construct Directory objects from dictionaries."""

        # pop children array from input dictionary object
        obj_children = obj.pop("children", [])
        # create new Directory object from remaining keys in obj
        directory = Directory(**obj)
        # create array of Directory objects from obj_children (recursive)
        children = [Directory._tree_builder(child) for child in obj_children]
        # insert children into new directory object
        directory.add_children(children)
        return directory

    @classmethod
    def init_from_json(cls, filename: str, root_name: str) -> Directory:
        """
        Initialise Directory object from JSON file. Adds all subsequent
        descendent Directory objects using recursion.

        ## Parameters

        `filename` (str)
            The path of the JSON file relative to the module.

        `root_name` (str)
            The key used in the top-level of the JSON file used to identify the
            object which is used to initialise the Directory object.

        ## Returns

        A Directory object corresponding to the object defined with the
        `root_name` key in the `filename` JSON file.

        ## Examples

        Consider the file `data.json` with the following contents:

        ``` json
        {
            "project": {
                "name": "project-name",
                "description": "Project directory",
                "children": [...]
            }
        }
        ```

        The following code converts this into nested Directory objects and
        renames the root Directory object to "new-project-name".

        >>> directory = Directory.init_from_json("data.json", "project")
        >>> directory.name = "new-project-name"
        """

        # read json file
        with open(filename, encoding="utf-8") as file:
            data = json.load(file)
        # access required root key in json object
        root_obj = data[root_name]
        # make Directory object using this root object
        return cls._tree_builder(root_obj)

    @property
    def name(self) -> str:
        """Get name attribute safely."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set name attribute safely."""
        # check that name is unique amongst children of parent Directory
        if self.parent is not None:
            for subdir in self.parent._children:
                # allow setting as own name (name is still unique)
                if self.name == value:
                    return
                # raise error if attempting to set as existing name
                if subdir.name == value:
                    raise ValueError(
                        f"A subdirectory with the name '{value}' "
                        f"already exists in '{self.parent.name}'"
                    )
        # update name attribute
        self._name = value

    @property
    def parent(self) -> Directory:
        """Get parent attribute safely."""
        return self._parent

    @property
    def level(self) -> int:
        """
        The number of direct ancestors between the current Directory and the
        root Directory object.

        ## Notes

        - Uses the fact that the root Directory object has `parent` attribute
        value of `None`.
        """
        counter = 0
        ancestor = self
        while not ancestor._is_root:
            counter += 1
            ancestor = ancestor.parent
        return counter

    def _add_child(self, child: Directory) -> None:
        """
        Add a single child to the current Directory.

        ## Notes

        - `name` attribute of `child` input must be unique amongst all children
        of the current Directory.
        """

        # check that name of child is unique amongst children of this object
        for subdir in self._children:
            if subdir.name == child.name:
                raise ValueError(
                    f"A subdirectory with the name '{child.name}' "
                    f"already exists in '{self.name}'"
                )
        # update parent attribute of child object
        child._parent = self
        # insert child into children array
        self._children.append(child)

    def add_children(self, *args: Union[Directory, List[Directory]]) -> None:
        """
        Adds any Directory objects contained in `args` to the `children` array.

        ## Parameters

        `*args` (Directory or List[Directory])
            Any number of Directory objects (or nested lists of Directory
            objects) which must be added as subdirectories of the current
            Directory.

        ## Returns

        No return value. Method inserts inputs into the `children` array
        attribute internally.

        ## Notes

        - All children in the `children` array attribute are sorted
        alphabetically by name after every call of this method. You should
        attempt to minimise the number of calls if possible.
        - This method calls the `_add_child()` method and so has the same
        requirements of inputs.

        ## Examples

        The following code demonstrates how you can combine and list Directory
        objects in any format and have them added to the `children` array.

        >>> root_directory = Directory("root")
        >>> dir_A = Directory("A")
        >>> dir_B = Directory("B")
        >>> dir_C = Directory("C")
        >>> root_directory.add_children(dir_A, [dir_B, [dir_C]])
        """

        # add children arguments
        for arg in args:
            if isinstance(arg, Directory):
                self._add_child(arg)
            elif isinstance(arg, list):
                self.add_children(*arg)
            else:
                raise ValueError(f"Input of type '{type(arg)}' is unsupported")
        # sort children alphabetically by name attribute
        self._children.sort(key=lambda child: child.name)

    @property
    def _is_root(self) -> bool:
        return self.parent is None

    @property
    def _is_last_child(self) -> bool:
        if self.parent is None:
            return None
        return self == self.parent._children[-1]

    def _tree(self, levels: int = 2) -> str:
        # prepare prefix string
        prefix = ""
        if not self._is_root:
            prefix += "└─ " if self._is_last_child else "├─ "
        # iterate up ancestry tree until root
        ancestor = self
        # must check that both parent and grandparent are not None so that
        # extra line isn't drawn
        while (
            ancestor.parent is not None and
            ancestor.parent.parent is not None
        ):
            # add to prefix accordingly
            if ancestor.parent._is_last_child:
                prefix = "   " + prefix
            else:
                prefix = "│  " + prefix
            # get next ancestor
            ancestor = ancestor.parent
        # construct 'tree' string output
        line = f"{prefix}📁 {self.name}"
        if levels > 1:
            for child in self._children:  # add children to output (recursive)
                line += "\n" + child._tree(levels=levels - 1)
        return line

    def tree(self, levels: int = 2) -> str:
        """
        Get plain text 'tree' representation of stucture as string.

        ## Parameters

        `levels` (int=2)
            The number of iterations 'down' the tree to go. Consider
            breadth-depth-search starting from the self object.
        """

        return self._tree(levels=levels)

    def generate_tree(self, root_path: str = "") -> None:
        """
        Realise the Python object as a real directory tree structure.

        ## Parameters

        `root_path` (str="")
            The path in which to generate the directory tree.
        """

        root_path = os.path.join(root_path, self.name)
        os.mkdir(root_path)
        for child in self._children:
            child.generate_tree(root_path=root_path)


def main():
    test_directory = Directory.init_from_json("templates.json", "test")

    # print(test_directory.tree(levels=3))
    test_directory.generate_tree()


if __name__ == "__main__":
    main()
