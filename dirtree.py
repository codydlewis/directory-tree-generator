"""
# Directory tree structure (dirtree)

This project provides code to convert a directory tree structure (defined in a
JSON file) into an actual directory tree at a defined location on your
computer.
"""

from __future__ import annotations
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
        self.children = []

    def __repr__(self) -> str:
        return f"Directory('{self.name}', {len(self.children)} children)"

    def __getitem__(self, key: str) -> Directory:
        """Get child Directory object by `name` attibute of children.
        Guaranteed unique."""

        for child in self.children:
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
            for subdir in self.parent.children:
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
        while ancestor.parent is not None:
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
        for subdir in self.children:
            if subdir.name == child.name:
                raise ValueError(
                    f"A subdirectory with the name '{child.name}' "
                    f"already exists in '{self.name}'"
                )
        # update parent attribute of child object
        child._parent = self
        # insert child into children array
        self.children.append(child)

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
        self.children.sort(key=lambda child: child.name)


def main():
    test_directory = Directory.init_from_json("templates.json", "test")

    print(test_directory["Test A"]["T"])


if __name__ == "__main__":
    main()
