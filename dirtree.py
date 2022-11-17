"""
# Directory tree structure (dirtree)

This project provides code to convert a directory tree structure (defined in a
JSON file) into an actual directory tree at a defined location on your
computer.
"""

from __future__ import annotations
from typing import Optional, Union, List


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
        self.parent = None
        self.children = []

    def __repr__(self) -> str:
        return f"Directory('{self.name}', {len(self.children)} children)"

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
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

    def _add_child(self, child: Directory) -> None:
        # check that name of child is unique amongst children of this object
        for subdir in self.children:
            if subdir.name == child.name:
                raise ValueError(
                    f"A subdirectory with the name '{child.name}' "
                    f"already exists in '{self.name}'"
                )
        # update parent attribute of child object
        child.parent = self
        # insert child into children array
        self.children.append(child)

    def add_children(self, *args: Union[Directory, List[Directory]]) -> None:
        # add children arguments
        for arg in args:
            if isinstance(arg, Directory):
                self._add_child(arg)
            elif isinstance(arg, List[Directory]):
                self.add_children(*arg)
            else:
                raise ValueError(f"Input of type '{type(arg)}' is unsupported")
        # sort children alphabetically by name attribute
        self.children.sort(key=lambda child: child.name)


def main():
    test_directory = Directory("Test")

    test2_directory = Directory("Test2")
    test3_directory = Directory("Test3")

    test_directory.add_children(test2_directory, test3_directory)


if __name__ == "__main__":
    main()
