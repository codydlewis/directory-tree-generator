"""
# Directory tree structure (dirtree)

This project provides code to convert a directory tree structure (defined in a
JSON file) into an actual directory tree at a defined location on your
computer.
"""

from __future__ import annotations
import datetime
import os
from typing import Optional, Union, List, Dict, Literal
import json
from math import inf
from urllib.parse import quote
import re
import yaml


def replace_all(string: str, mapping: Dict[str, str]) -> str:
    """
    Replace all keys with values from `mapping` in `string`.

    ## Parameters

    `string` (str)
        The string which replacements within are to be made.

    `mapping` (Dict[str, str])
        The replacements to make in `string`. Keys in the dictionary
        correspond to substrings which are matched in `string`, and values in
        the dictionary are substrings which replace the corresponding key in
        `string`.
    """

    for key, value in mapping.items():
        value = "" if value is None else value
        string = string.replace(key, value)
    return string


class Directory:
    """
    Directory objects represent digital 'folders' which contain other folders
    and files.
    """

    def __init__(
        self, name: str, description: Optional[str] = None,
        icon: str = "bx-folder", tags: List[str] = None
    ) -> None:
        self._name = name
        self.description = description
        self.icon = icon
        self.tags = [] if tags is None else tags
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
    def _build_from_object(obj: Dict, /) -> Directory:
        """Recursively construct Directory objects from dictionaries."""

        # pop children array from input dictionary object
        obj_children = obj.pop("children", [])
        # create new Directory object from remaining keys in obj
        directory = Directory(**obj)
        # create array of Directory objects from obj_children (recursive)
        children = [
            Directory._build_from_object(child)
            for child in obj_children]
        # insert children into new directory object
        directory.add_children(children)
        return directory

    @classmethod
    def import_json(cls, filename: str, root_name: str) -> Directory:
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

        >>> directory = Directory.import_json("data.json", "project")
        >>> directory.name = "new-project-name"
        """

        # read json file
        with open(filename, encoding="utf-8") as file:
            data = json.load(file)
        # access required root key in json object
        root_obj = data[root_name]
        # make Directory object using this root object
        return cls._build_from_object(root_obj)

    @classmethod
    def import_yaml(cls, filename: str, root_name: str) -> Directory:
        """
        Initialise Directory object from YAML file. Adds all subsequent
        descendent Directory objects using recursion.

        ## Parameters

        `filename` (str)
            The path of the YAML file relative to the module.

        `root_name` (str)
            The key used in the top-level of the YAML file used to identify the
            object which is used to initialise the Directory object.

        ## Returns

        A Directory object corresponding to the object defined with the
        `root_name` key in the `filename` YAML file.

        ## Examples

        Consider the file `data.yaml` with the following contents:

        ``` yaml
        project:
            name: project-name
            description: Project directory
            children: [...]
        ```

        The following code converts this into nested Directory objects and
        renames the root Directory object to "new-project-name".

        >>> directory = Directory.import_yaml("data.yaml", "project")
        >>> directory.name = "new-project-name"
        """

        # read json file
        with open(filename, encoding="utf-8") as file:
            data = yaml.safe_load(file)
        # access required root key in json object
        root_obj = data[root_name]
        # make Directory object using this root object
        return cls._build_from_object(root_obj)

    @staticmethod
    def _build_from_directory(path: str):
        # create Directory object with name as last directory in path
        directory = Directory(os.path.split(path)[-1])
        # ----- children
        # get complete paths for all subdirectorys of the directory at path
        children_paths = [
            os.path.join(path, subdir)
            for subdir in os.listdir(path)
            if os.path.isdir(os.path.join(path, subdir))
        ]
        # create list of children Directories (recursive)
        children = [
            Directory._build_from_directory(child_path)
            for child_path in children_paths
        ]
        # add children to this directory
        directory.add_children(children)
        # ----- details
        # get the readme file in this direcctory
        potential_files = [
            subdir
            for subdir in os.listdir(path)
            if os.path.isfile(os.path.join(path, subdir))
        ]
        for file in potential_files:
            filename_components = file.rsplit(".", maxsplit=1)
            # check if it is a readme file
            if filename_components[0].lower() == "readme":
                readme_path = os.path.join(path, ".".join(filename_components))
                # read readme file and get frontmatter
                with open(readme_path, encoding="utf-8") as readme_file:
                    readme_content = readme_file.read()
                readme_frontmatter = re.match(
                    r"---\n((.*\n)*)---\n", readme_content)
                # check that frontmatter exists
                if readme_frontmatter is not None:
                    readme_frontmatter = readme_frontmatter.group(1)
                    # parse yaml
                    readme_yaml = yaml.safe_load(readme_frontmatter)
                    # update directory object properties
                    if "directory_icon" in readme_yaml.keys():
                        directory.icon = readme_yaml["directory_icon"]
                    if "directory_description" in readme_yaml.keys():
                        directory.description = readme_yaml[
                            "directory_description"]
                    if "directory_tags" in readme_yaml.keys():
                        directory.tags = readme_yaml["directory_tags"]
                # only consider the first readme file
                break
        return directory

    @classmethod
    def import_directory(cls, root_path: str) -> Directory:
        """
        Initialise Directory object from real directory. Adds all subsequent
        descendent Directory objects using recursion.

        ## Parameters

        `root_path` (str)
            The path of the real directory relative to the module for which the
            Directory object is to be generated from.

        ## Returns

        A Directory object corresponding to the directory, and all descendent
        subdirectories, at `root_path`.

        ## Examples

        The following code converts the directory with name "project" into a
        Directory object.

        >>> directory = Directory.import_directory("project")
        """

        return Directory._build_from_directory(root_path)

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

    def tree(self, levels: int = inf) -> str:
        """
        Get plain text 'tree' representation of stucture as string.

        ## Parameters

        `levels` (int=2)
            The number of iterations 'down' the tree to go. Consider
            breadth-depth-search starting from the self object.
        """

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
                line += "\n" + child.tree(levels=levels - 1)
        return line

    @property
    def ancestors(self) -> List[Directory]:
        """Returns a list of ancestors from root to current directory
        (inclusive)."""

        if self._is_root:
            return [self]
        return self.parent.ancestors + [self]

    def _export_readme(
        self, template_path: str, directory_path: str,
        custom_placeholders: dict
    ) -> str:
        # get readme template file
        with open(template_path, encoding="utf-8") as template_file:
            readme_contents = template_file.read()

        # replace variables in template to produce final readme string
        replacements = {
            "[DIRECTORY_NAME]": self.name,
            "[DIRECTORY_ICON]": self.icon,
            "[DIRECTORY_DESCRIPTION]": self.description,
            "[DIRECTORY_TAGS_LIST]": (
                f"`{'` `'.join(self.tags)}`"
            ) if len(self.tags) > 0 else "",
            "[DIRECTORY_FRONTMATTER]": (
                f'directory_name: {self.name}\n'
                f'directory_icon: {self.icon}\n'
                f'directory_description: {self.description}\n'
                f'directory_tags_list: {self.tags}'
            ),
            "[CURRENT_DATE]": datetime.date.today().isoformat(),
            "[CURRENT_TIME]": datetime.datetime.now().time().isoformat(
                timespec="seconds"),
            "[CURRENT_DATETIME]": datetime.datetime.isoformat(
                datetime.datetime.now(), sep=" ", timespec="minutes"),
            "[DIRECTORY_CONTENTS]": (
                '- ' + ' > '.join([
                    (
                        f'<i class="bx {ancestor.icon}"></i> '
                        f'**[{ancestor.name}]('
                        f'{"../" * (len(self.ancestors) - index)}'
                        f'{quote(ancestor.name)}/README.md)**'
                    ) for index, ancestor in enumerate(self.ancestors)
                ]) + '\n' + '\n'.join([
                    (
                        f'  - <i class="bx {child.icon}"></i> '
                        f'**[{child.name}]({quote(child.name)}/README.md)**: '
                        f'{child.description}'
                    ) for child in self._children
                ])
            ),
        }
        replacements |= custom_placeholders
        readme_contents = replace_all(readme_contents, replacements)

        # replace all 'extra' newlines with only a double newline
        readme_contents = re.sub("\n{3,}", "\n\n", readme_contents)

        # write to file at path
        readme_path = os.path.join(directory_path, "README.md")
        with open(readme_path, mode="w", encoding="utf-8") as readme_file:
            readme_file.write(readme_contents)

    def export_directory(
        self, root_path: str = "", custom_placeholders: dict = None
    ) -> None:
        """
        Realise the Python object as a real directory tree structure.

        ## Parameters

        `root_path` (str="")
            The path in which to generate the directory tree.
        """

        # make custom_placeholders default to empty dictionary
        if custom_placeholders is None:
            custom_placeholders = {}

        root_path = os.path.join(root_path, self.name)
        os.mkdir(root_path)
        for child in self._children:
            child.export_directory(
                root_path=root_path, custom_placeholders=custom_placeholders)
        # create readme
        self._export_readme(
            "readme-template.txt", root_path, custom_placeholders)

    def _objectify(self) -> dict:
        return {
            "name": self.name,
            "icon": self.icon,
            "description": self.description,
            "tags": self.tags,
            "children": [child._objectify() for child in self._children]
        }

    def export_yaml(
        self, filename: str, root_name: str = "root",
        existing_file_method: Literal["add", "overwrite", "error"] = "add"
    ) -> None:
        """
        Exports the python Directory object as a YAML file saved at `filename`
        under the root-level name `root_name`.
        """

        # add to existing file
        if os.path.exists(filename) and existing_file_method == "add":
            # read existing file
            with open(filename, encoding="utf-8") as file:
                yaml_data: dict = yaml.safe_load(file)
            # add self object to existing file contents
            if root_name in yaml_data.keys():
                raise ValueError(
                    f"Name '{root_name}' already exists in '{filename}'"
                )
            yaml_data[root_name] = self._objectify()
            # export everything back into file
            with open(filename, mode="w", encoding="utf-8") as file:
                yaml.dump(yaml_data, file)
        # raise error for attempting to overwrite existing file
        elif os.path.exists(filename) and existing_file_method == "error":
            raise FileExistsError(
                f"Attempting to overwrite contents of {filename}\n"
                f"when existing_file_method is 'error'")
        # write to new file
        else:
            with open(filename, mode="w", encoding="utf-8") as file:
                yaml.dump({root_name: self._objectify()}, file)

    def export_json(
        self, filename: str, root_name: str = "root",
        existing_file_method: Literal["add", "overwrite", "error"] = "add"
    ) -> None:
        """
        Eports the python Directory object as a JSON file save at `filename`
        under the root-level name `root_name`.
        """

        # add to existing file
        if os.path.exists(filename) and existing_file_method == "add":
            # read existing file
            with open(filename, encoding="utf-8") as file:
                json_data: dict = json.load(file)
            # add self object to existing file contents
            if root_name in json_data.keys():
                raise ValueError(
                    f"Name '{root_name}' already exists in '{filename}'"
                )
            json_data[root_name] = self._objectify()
            # export everything back into file
            with open(filename, mode="w", encoding="utf-8") as file:
                file.write(json.dumps(json_data))
        # raise error for attempting to overwrite existing file
        elif os.path.exists(filename) and existing_file_method == "error":
            raise FileExistsError(
                f"Attempting to overwrite contents of {filename}\n"
                f"when existing_file_method is 'error'")
        # write to new file
        else:
            with open(filename, mode="w", encoding="utf-8") as file:
                file.write(json.dumps({root_name: self._objectify()}))
